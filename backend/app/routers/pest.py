"""
Pest Vision Router
- Analyze crop images for pest/disease detection
- Uses Claude Vision for image analysis
"""
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from pydantic import BaseModel
from app.services.bedrock import bedrock_service

router = APIRouter(prefix="/pest", tags=["Pest Vision"])


class PestAnalysisResult(BaseModel):
    """Result of pest/disease analysis"""
    detected: bool
    pest_name: Optional[str] = None
    pest_name_hi: Optional[str] = None
    confidence_pct: int
    severity: str  # "mild", "moderate", "severe"
    description: str
    description_hi: str
    treatment_suggestions: list[str]
    treatment_suggestions_hi: list[str]
    prevention_tips: list[str]


PEST_ANALYSIS_PROMPT = """You are an agricultural expert analyzing a crop image for pests and diseases.

Analyze the image and identify:
1. Is there any pest infestation or plant disease visible?
2. If yes, what is it? (Common Indian crop pests/diseases)
3. How severe is it? (mild/moderate/severe)
4. What treatment do you recommend?
5. Prevention tips for the future

Respond in this exact JSON format:
{
  "detected": true/false,
  "pest_name": "Name of pest/disease in English",
  "pest_name_hi": "Name in Hindi",
  "confidence_pct": 85,
  "severity": "mild|moderate|severe",
  "description": "Description in English",
  "description_hi": "Description in Hindi",
  "treatment_suggestions": ["Treatment 1", "Treatment 2"],
  "treatment_suggestions_hi": ["उपचार 1", "उपचार 2"],
  "prevention_tips": ["Prevention tip 1", "Prevention tip 2"]
}

Common Indian crop pests/diseases to look for:
- Soybean: Yellow mosaic virus, Pod borer, Stem fly
- Wheat: Rust, Aphids, Loose smut
- Rice: Blast, Stem borer, Brown planthopper
- Cotton: Bollworm, Whitefly, Leaf curl virus
"""


@router.post("/analyze", response_model=PestAnalysisResult)
async def analyze_crop_image(
    image: UploadFile = File(..., description="Crop image to analyze"),
    crop: Optional[str] = Form(None, description="Crop type if known"),
    household_id: Optional[str] = Form(None, description="Household ID"),
):
    """Analyze a crop image for pest/disease detection"""
    
    # Read and encode image
    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="Image too large. Max 10MB.")
    
    # Determine media type
    content_type = image.content_type or "image/jpeg"
    if content_type not in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
        raise HTTPException(status_code=400, detail="Unsupported image format. Use JPEG, PNG, WebP, or GIF.")
    
    # Encode to base64
    image_b64 = base64.standard_b64encode(contents).decode("utf-8")
    
    # Build message with image for Claude Vision
    crop_context = f"The farmer says this is a {crop} crop." if crop else "Crop type unknown."
    
    messages = [{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": content_type,
                    "data": image_b64,
                },
            },
            {
                "type": "text",
                "text": f"Analyze this crop image for pests or diseases. {crop_context}\n\nRespond with ONLY the JSON output.",
            },
        ],
    }]
    
    # Call Claude Vision
    response = bedrock_service.invoke(
        messages=messages,
        system_prompt=PEST_ANALYSIS_PROMPT,
        max_tokens=1024,
        temperature=0.3,
    )
    
    # Parse JSON response
    try:
        import json
        # Find JSON in response
        json_str = response.strip()
        if "```" in json_str:
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
        
        data = json.loads(json_str)
        return PestAnalysisResult(**data)
    except Exception as e:
        # Return default "healthy" response if parsing fails
        return PestAnalysisResult(
            detected=False,
            confidence_pct=50,
            severity="mild",
            description="Could not analyze image clearly. Please try with a clearer, well-lit photo.",
            description_hi="छवि स्पष्ट नहीं है। कृपया साफ और अच्छी रोशनी में फोटो लें।",
            treatment_suggestions=["Take a clearer photo and try again"],
            treatment_suggestions_hi=["साफ फोटो लें और दोबारा कोशिश करें"],
            prevention_tips=["Regular crop monitoring", "Proper irrigation"],
        )

