from pymodbus.client import AsyncModbusTcpClient
import asyncio
import os
import asyncpg
from dotenv import load_dotenv
import socketio
import pytz
from datetime import datetime
import json
import RPi.GPIO as GPIO


load_dotenv()

SERVERURL = 'http://localhost:3000'
sio = socketio.AsyncClient()


@sio.event
async def connect():
    print("Connected to WebSocket server")

@sio.event
async def disconnect():
    print("Disconnected from WebSocket server")

async def getSignals() -> list:
    connection: asyncpg.Connection = await asyncpg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        password=os.getenv("DB_PASSWORD"),
        user=os.getenv("DB_USER")
    )
    rows = await connection.fetch("select * from tpm")
    await connection.close()
    return rows

async def connectClient(host: str, port: int) -> AsyncModbusTcpClient:
    client = AsyncModbusTcpClient(host=host, port=port)
    await client.connect()
    return client

def normalizeVoltage(v):
    VT = 1
    return str(round(v*VT*0.1, 2))

def normalizeCurrent(c):
    CT = 1
    return str(round(c*CT*0.001, 2))

def normalizeFrequency(f):
    return str(round(f*0.01, 2))

def normalizePowerFactor(pf):
    return str(round(pf*0.001, 2))

async def main():
    client = await connectClient(host="localhost", port=5020)
    print("Client connection is "+str(client.connected))
    signalList = await getSignals()
    print(f"Total {len(signalList)} signals found")
    signalValues = {}
    sio.connect(SERVERURL)
    storeConnection: asyncpg.Connection = await asyncpg.connect(
        host="localhost",
        port="5432",
        database=os.getenv("DB_NAME_LOCAL"),
        password=os.getenv("DB_PASSWORD_LOCAL"),
        user="devgadbadr"
    )
    # Set them as input with internal pull-up resistors
    pins = [17, 27, 22]
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for p in pins:
        GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    turkey_tz = pytz.timezone("Europe/Istanbul")
    while client.connected:
        # Read gens status 
        states = {p: GPIO.input(p) for p in pins}
        print(states)

        gen1CurrentState = states[17] 
        gen2CurrentState = 0
        gen3CurrentState = states[22]
        
        signalValues['gen1'] = gen1CurrentState
        signalValues['gen2'] = gen2CurrentState
        signalValues['gen3'] = gen3CurrentState

        query = """
        SELECT DISTINCT ON (gen) gen, state, timestamp
        FROM gens
        WHERE gen IN ('gen1', 'gen2', 'gen3')
        ORDER BY gen, timestamp DESC
        """
        async with storeConnection.transaction():
            rows = await storeConnection.fetch(query)
        
        ts = datetime.now(turkey_tz)
        
        latest = {row['gen']: row for row in rows}
        gen1last = latest.get('gen1')
        gen2last = latest.get('gen2')
        gen3last = latest.get('gen3')
        gen1state = gen1last[1]
        gen2state = gen2last[1]
        gen3state = gen3last[1]

        if gen1CurrentState: #gen 1 off its gpio is 1
            if gen1state:
                await storeConnection.execute("insert into gens (status,timestamp,gen,state) values ($1,$2,$3,$4)",'gen 1 off',ts,'gen1',False)
        else: #gen 1 on its gpio is 0
            if not gen1state:
                await storeConnection.execute("insert into gens (status,timestamp,gen,state) values ($1,$2,$3,$4)",'gen 1 on',ts,'gen1',True)

        if gen2CurrentState: #gen 2 off its gpio is 1
            if gen2state:
                await storeConnection.execute("insert into gens (status,timestamp,gen,state) values ($1,$2,$3,$4)",'gen 2 off',ts,'gen2',False)
        else: #gen 2 on its gpio is 0
            if not gen2state:
                await storeConnection.execute("insert into gens (status,timestamp,gen,state) values ($1,$2,$3,$4)",'gen 2 on',ts,'gen2',True)

        if gen3CurrentState: #gen 2 off its gpio is 1
            if gen3state:
                await storeConnection.execute("insert into gens (status,timestamp,gen,state) values ($1,$2,$3,$4)",'gen 3 off',ts,'gen3',False)
        else: #gen 2 on its gpio is 0
            if not gen3state:
                await storeConnection.execute("insert into gens (status,timestamp,gen,state) values ($1,$2,$3,$4)",'gen 3 on',ts,'gen3',True)

        # Read L1, L2, L3 Voltage
        rr = await client.read_holding_registers(4000,3)
        signalValues['L1 Voltage'] = normalizeVoltage(rr.registers[0]) if rr.registers else ""
        signalValues['L2 Voltage'] = normalizeVoltage(rr.registers[1]) if rr.registers else ""
        signalValues['L3 Voltage'] = normalizeVoltage(rr.registers[2]) if rr.registers else ""

        # Read L1, L2, L3 Current
        rr = await client.read_holding_registers(4024,4)
        signalValues['L1 Current'] = normalizeCurrent(rr.registers[0]) if rr.registers else ""
        signalValues['L2 Current'] = normalizeCurrent(rr.registers[1]) if rr.registers else ""
        signalValues['L3 Current'] = normalizeCurrent(rr.registers[2]) if rr.registers else ""
        signalValues['Neutral Current'] = normalizeCurrent(rr.registers[3]) if rr.registers else ""

        # Read Frequency
        rr = await client.read_holding_registers(4040,3)
        signalValues['L1 Frequency'] = normalizeFrequency(rr.registers[0]) if rr.registers else ""
        signalValues['L2 Frequency'] = normalizeFrequency(rr.registers[1]) if rr.registers else ""
        signalValues['L3 Frequency'] = normalizeFrequency(rr.registers[2]) if rr.registers else ""

        # Read Power Factor
        rr = await client.read_holding_registers(4043,4)
        signalValues['L1 Power Factor'] = normalizePowerFactor(rr.registers[0]) if rr.registers else ""
        signalValues['L2 Power Factor'] = normalizePowerFactor(rr.registers[1]) if rr.registers else ""
        signalValues['L3 Power Factor'] = normalizePowerFactor(rr.registers[2]) if rr.registers else ""
        signalValues['Total Power Factor'] = normalizePowerFactor(rr.registers[3]) if rr.registers else ""

        # Read Active Power
        rr = await client.read_holding_registers(4140,8)
        if rr.registers and len(rr.registers) >= 2:
            high, low = rr.registers[0], rr.registers[1]
            value = (high << 16) | low
        else:
            value = 0
        signalValues['L1 Active Power'] = value
        if rr.registers and len(rr.registers) >= 4:
            high, low = rr.registers[2], rr.registers[3]
            value = (high << 16) | low
        else:
            value = 0
        signalValues['L2 Active Power'] = value
        if rr.registers and len(rr.registers) >= 6:
            high, low = rr.registers[4], rr.registers[5]
            value = (high << 16) | low
        else:
            value = 0
        signalValues['L3 Active Power'] = value
        if rr.registers and len(rr.registers) >= 8:
            high, low = rr.registers[6], rr.registers[7]
            value = (high << 16) | low
        else:
            value = 0
        signalValues['Total Active Power'] = value

        # Read Reactive Power
        rr = await client.read_holding_registers(4162,8)
        if rr.registers and len(rr.registers) >= 2:
            high, low = rr.registers[0], rr.registers[1]
            value = (high << 16) | low
        else:
            value = 0
        signalValues['L1 Reactive Power'] = value
        if rr.registers and len(rr.registers) >= 4:
            high, low = rr.registers[2], rr.registers[3]
            value = (high << 16) | low
        else:
            value = 0
        signalValues['L2 Reactive Power'] = value
        if rr.registers and len(rr.registers) >= 6:
            high, low = rr.registers[4], rr.registers[5]
            value = (high << 16) | low
        else:
            value = 0
        signalValues['L3 Reactive Power'] = value
        if rr.registers and len(rr.registers) >= 8:
            high, low = rr.registers[6], rr.registers[7]
            value = (high << 16) | low
        else:
            value = 0
        signalValues['Total Reactive Power'] = value

        #  Read Apparent Power
        rr = await client.read_holding_registers(4184,8)
        if rr.registers and len(rr.registers) >= 2:
            high, low = rr.registers[0], rr.registers[1]
            value = (high << 16) | low
        else:
            value = 0
        signalValues['L1 Apparent Power'] = value
        if rr.registers and len(rr.registers) >= 4:
            high, low = rr.registers[2], rr.registers[3]
            value = (high << 16) | low
        else:
            value = 0
        signalValues['L2 Apparent Power'] = value
        if rr.registers and len(rr.registers) >= 6:
            high, low = rr.registers[4], rr.registers[5]
            value = (high << 16) | low
        else:
            value = 0
        signalValues['L3 Apparent Power'] = value
        if rr.registers and len(rr.registers) >= 8:
            high, low = rr.registers[6], rr.registers[7]
            value = (high << 16) | low
        else:
            value = 0
        signalValues['Total Apparent Power'] = value

        # Read Total Active Import Energy
        rr = await client.read_holding_registers(4222,4)
        if rr.registers and len(rr.registers) >= 4:
            h3, h2, h1, l = rr.registers[0], rr.registers[1], rr.registers[2], rr.registers[3]
            energy_wh = (h3 << 48) | (h2 << 32) | (h1 << 16) | l   
        else:
            energy_wh = 0
        signalValues['Total Active Import Energy'] = energy_wh

        # Read Total Active Export Energy
        rr = await client.read_holding_registers(4238,4)
        if rr.registers and len(rr.registers) >= 4:
            h3, h2, h1, l = rr.registers[0], rr.registers[1], rr.registers[2], rr.registers[3]
            energy_wh = (h3 << 48) | (h2 << 32) | (h1 << 16) | l
        else:
            energy_wh = 0
        signalValues['Total Active Export Energy'] = energy_wh

        # Read Total Inductive Energy
        rr = await client.read_holding_registers(4254,4)
        if rr.registers and len(rr.registers) >= 4:
            h3, h2, h1, l = rr.registers[0], rr.registers[1], rr.registers[2], rr.registers[3]
            energy_varh = (h3 << 48) | (h2 << 32) | (h1 << 16) | l
        else:
            energy_varh = 0
        signalValues['Total Inductive Energy'] = energy_varh

        # Read Total Capacitive Energy
        rr = await client.read_holding_registers(4270,4)
        if rr.registers and len(rr.registers) >= 4:
            h3, h2, h1, l = rr.registers[0], rr.registers[1], rr.registers[2], rr.registers[3]
            energy_varh = (h3 << 48) | (h2 << 32) | (h1 << 16) | l
        else:
            energy_varh = 0
        signalValues['Total Capacitive Energy'] = energy_varh

        # Read Total Apparent Energy
        rr = await client.read_holding_registers(4292,4)
        if rr.registers and len(rr.registers) >= 4:
            h3, h2, h1, l = rr.registers[0], rr.registers[1], rr.registers[2], rr.registers[3]
            energy_vah = (h3 << 48) | (h2 << 32) | (h1 << 16) | l
        else:
            energy_vah = 0
        signalValues['Total Apparent Energy'] = energy_vah

        # for key, value in signalValues.items():
        #     print(f"{key}: {value}")

        if sio.connected:
            await sio.emit("modbus-data", signalValues)
        else:
            print("WebSocket not connected No Data Sent... Will Try to Reconnect")
            try:
                await sio.connect(SERVERURL)
            except Exception as e:
                print("Reconnection failed:", e)

        # Logic to store data to database
        # It should check last reading against current time, if more than one hour it stores , if not just passes
        lastReading = await storeConnection.fetchval("select timestamp from tpmreading order by timestamp desc limit 1")
        print("last reading: ",lastReading)

        payload = json.dumps(signalValues)
        if not lastReading:
            await storeConnection.execute("INSERT INTO tpmreading (data, timestamp) VALUES ($1, $2)",payload, ts)
            print("inserted first readings")
        else:
            now = datetime.now(turkey_tz)
            diff = now - lastReading
            seconds = diff.total_seconds()
            print(round(seconds))
            # log every 10 minutes
            if seconds >= 60*10:
                await storeConnection.execute("INSERT INTO tpmreading (data, timestamp) VALUES ($1, $2)",payload, ts)
                print("inserted a reading: ",now)

        print("-"*20)
        await asyncio.sleep(2)


    await client.close()
    await sio.disconnect()
    print("Client Disconnected")
    
asyncio.run(main())