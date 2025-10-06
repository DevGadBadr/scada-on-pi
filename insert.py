import asyncio
import asyncpg
from tpmrows import tpm_registers
from dotenv import load_dotenv
import os

load_dotenv()

async def makeConnection():
    connection: asyncpg.Connection = await asyncpg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        password=os.getenv("DB_PASSWORD"),
        user=os.getenv("DB_USER")
    )
    return connection

async def main():
    connection: asyncpg.Connection = await makeConnection()
    params = [(True, r[1], r[2], r[3], r[4], str(r[5]), r[6]) for r in tpm_registers]
    query ="insert into tpm (enabled, address, parameter, datatype, readwrite, multiplier, unit)" \
    "values ($1,$2,$3,$4,$5,$6,$7) "\
    "on conflict (address) do nothing "
    async with connection.transaction():
        await connection.executemany(query,params)
asyncio.run(main())