#/bin/bash

python3 -m benchexec.test_tool_info \
    --full-access-dir results/ \
    --read-only-dir config \
    --read-only-dir defaults \
    --read-only-dir models \
    --read-only-dir tasks \
    --read-only-dir / \
    --debug tools.xfta2
