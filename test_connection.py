
import os
from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()

try:
    print("Connecting without TLS...", flush=True)

    db = FalkorDB(
        host=os.environ["FALKORDB_HOST"],
        port=int(os.getenv("FALKORDB_PORT", "57993")),
        username=os.environ["FALKORDB_USERNAME"],
        password=os.environ["FALKORDB_PASSWORD"],
        ssl=False,
        socket_connect_timeout=5,
        socket_timeout=5,
    )

    print("Checking database...", flush=True)
    db.connection.ping()

    graph = db.select_graph(
        os.getenv("FALKORDB_GRAPH", "keystone")
    )
    result = graph.query(
        'RETURN "KEYSTONE connected!" AS message'
    )

    print("SUCCESS:", result.result_set, flush=True)

except Exception as error:
    print("FAILED:", type(error).__name__, str(error), flush=True)
