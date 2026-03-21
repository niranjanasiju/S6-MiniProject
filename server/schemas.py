from pydantic import BaseModel, Field
from typing import List, Optional


class PredictRequest(BaseModel):
    current_drugs : List[str] = Field(
        ...,
        description = "List of drugs the patient is currently taking",
        example     = ["warfarin", "metformin"],
    )
    new_drug : str = Field(
        ...,
        description = "The new drug to evaluate for interactions",
        example     = "aspirin",
    )
    age : int = Field(
        default     = 40,
        description = "Patient age in years",
        example     = 65,
    )
    gender : str = Field(
        default     = "male",
        description = "Patient gender: male | female | other",
        example     = "male",
    )

class SideEffectResult(BaseModel):
    effect      : str
    probability : float = Field(description="Confidence % (0–100)")
    severity    : int   = Field(description="Severity weight (1–10)")

class PairResult(BaseModel):
    pair           : str
    safety_score   : Optional[float]   = None
    risk_tier      : Optional[str]     = Field(None, description="SAFE | CAUTION | AVOID")
    side_effects   : Optional[List[SideEffectResult]] = None
    ai_explanation : Optional[str]     = None
    error          : Optional[str]     = None

class PredictResponse(BaseModel):
    new_drug        : str
    current_drugs   : List[str]
    overall_verdict : str   = Field(description="Worst-case verdict: SAFE | CAUTION | AVOID")
    overall_score   : float = Field(description="Worst-case safety score (0–100)")
    pairs           : List[PairResult]

class ADRRequest(BaseModel):
    drug_name : str = Field(
        ...,
        description = "Generic drug name to analyse",
        example     = "aspirin",
    )
    threshold : float = Field(
        default     = 0.5,
        description = "Minimum confidence (0–1) for a side effect to be included",
        example     = 0.5,
    )

class ADRSideEffect(BaseModel):
    effect      : str
    probability : float = Field(description="Confidence % (0–100)")
    category    : str   = Field(description="Body system category")

class ADRResponse(BaseModel):
    drug           : str
    threshold      : float
    targets        : List[str] = Field(description="Biological protein targets")
    pathways       : List[str] = Field(description="Affected biological pathways")
    side_effects   : List[ADRSideEffect]
    ai_explanation : str