from pymodbus.server import ModbusSimulatorServer
import asyncio

async def run():
    simulator = ModbusSimulatorServer(
        modbus_server="myserver",
        modbus_device="tpm04",
        http_host="localhost",
        http_port=8080,
        log_file="server.log",
        json_file="setup.json"
    )
    print("Starting Modbus simulator server...")
    await simulator.run_forever()
    print("Server stopped")
asyncio.run(run())