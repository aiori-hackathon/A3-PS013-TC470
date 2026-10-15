from datetime import datetime

from pydantic import BaseModel


class ParseErrorResponse(BaseModel):
    id: str
    evidence_file_id: str
    case_id: str
    line_number: int
    raw_line: str
    reason: str
    parser_name: str
    created_at: datetime
    evidence_filename: str

    model_config = {"from_attributes": True}


class ParsingGapResponse(BaseModel):
    id: str
    evidence_file_id: str
    gap_start_line: int | None
    gap_end_line: int | None
    description: str
    created_at: datetime
    evidence_filename: str

    model_config = {"from_attributes": True}


class ParseIssuesResponse(BaseModel):
    parse_errors: list[ParseErrorResponse]
    parsing_gaps: list[ParsingGapResponse]
