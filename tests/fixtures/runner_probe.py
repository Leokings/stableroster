# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Release preflight only; not a Portal primitive."""

from genlayer import *


class ReleaseRunnerProbe(gl.Contract):
    value: u256
    seen_at: str

    def __init__(self):
        self.value = u256(0)
        self.seen_at = ""

    @gl.public.write
    def set_value(self, value: u256) -> None:
        self.value = value
        self.seen_at = str(gl.message_raw["datetime"])

    @gl.public.view
    def get_value(self) -> u256:
        return self.value

    @gl.public.view
    def get_timestamp(self) -> str:
        return self.seen_at
