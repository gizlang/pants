# Copyright 2022 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import annotations

import dataclasses
import datetime
import re
import string
from typing import Any

from pants.backend.tools.preamble.subsystem import PreambleSubsystem
from pants.core.goals.fmt import FmtFilesRequest, FmtResult, Partitions
from pants.engine.fs import CreateDigest, Digest, DigestContents, Snapshot
from pants.engine.rules import Get, collect_rules, rule
from pants.util.logging import LogLevel
from pants.util.memo import memoized


class PreambleRequest(FmtFilesRequest):
    tool_subsystem = PreambleSubsystem


@memoized
def _template_checker_regex(template: str) -> re.Pattern:
    maybe_shebang = r"(#!.*\n)?"
    subbed = string.Template(template).safe_substitute(year=r"====YEAR====")
    raw_regex = re.escape(subbed).replace("====YEAR====", r"\d{4}")
    return re.compile(maybe_shebang + raw_regex)


@memoized
def _substituted_template(template: str) -> str:
    return string.Template(template).safe_substitute(year=datetime.date.today().year)


@rule
async def partition_inputs(
    request: PreambleRequest.PartitionRequest, preamble_subsystem: PreambleSubsystem
) -> Partitions[Any]:
    if preamble_subsystem.skip:
        return Partitions()

    return Partitions.single_partition(
        sorted(preamble_subsystem.get_template_by_path(request.files))
    )


@rule(desc="Add preambles", level=LogLevel.DEBUG)
async def preamble_fmt(
    request: PreambleRequest.Batch, preamble_subsystem: PreambleSubsystem
) -> FmtResult:
    template_by_path = preamble_subsystem.get_template_by_path(request.snapshot.files)
    digest_contents = await Get(DigestContents, Digest, request.snapshot.digest)
    contents_by_path = {file_content.path: file_content for file_content in digest_contents}

    for path, template in template_by_path.items():
        regex = _template_checker_regex(template)
        file_content = contents_by_path[path].content
        if not regex.match(file_content.decode("utf-8")):
            new_content = _substituted_template(template).encode("utf-8") + file_content
            contents_by_path[path] = dataclasses.replace(
                contents_by_path[path], content=new_content
            )

    output_snapshot = await Get(Snapshot, CreateDigest(contents_by_path.values()))

    return FmtResult(
        input=request.snapshot,
        output=output_snapshot,
        stdout="",
        stderr="",
        tool_name=request.tool_name,
    )


def rules():
    return [
        *collect_rules(),
        *PreambleRequest.rules(),
    ]
