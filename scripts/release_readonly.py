"""Read-only StudioNet RPC helpers. No key loading and no transaction submission."""

import json
import time
from urllib import request

from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from genlayer_py.contracts.utils import make_calldata_object
from genlayer_py.types import TransactionHashVariant


RPC = "https://studio.genlayer.com/api"


def rpc(method, params):
    if method not in {"eth_chainId", "eth_getTransactionCount", "eth_getTransactionByHash",
                      "gen_call", "gen_getContractCode", "gen_getContractSchema"}:
        raise ValueError("read_only_rpc_method_required")
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for attempt in range(3):
        try:
            call = request.Request(RPC, data=body, headers={"Content-Type": "application/json",
                                   "Accept": "application/json", "User-Agent": "genlayer-py"})
            with request.urlopen(call, timeout=45) as response:
                raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ValueError("oversized_rpc_response")
            decoded = json.loads(raw)
            if decoded.get("error"):
                raise ValueError("rpc_error: " + str(decoded["error"].get("code")))
            return decoded["result"]
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))


def read_public(address, method, args, sender):
    data = serialize([calldata.encode(make_calldata_object(method=method, args=args)), b"\x00"])
    result = rpc("gen_call", [{"type": "read", "to": address, "from": sender, "data": data,
                              "transaction_hash_variant": TransactionHashVariant.LATEST_FINAL.value}])
    return calldata.decode(bytes.fromhex(result.removeprefix("0x")))
