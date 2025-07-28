"""
Core ontology parser and model for Business OS.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from dataclasses import dataclass
from enum import Enum


class DataType(str, Enum):
    """Supported data types in the ontology."""
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ENUM = "enum"
    LIST = "list"
    DICT = "dict"
    RANGE = "range"
    DATETIME = "datetime"


@dataclass
class PropertyDefinition:
    """Definition of a property in the ontology."""
    name: str
    data_type: DataType
    constraints: List[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = []


@dataclass
class Constraint:
    """Business constraint definition."""
    expression: str
    description: Optional[str] = None
    severity: str = "error"  # error, warning, info


@dataclass
class JourneyStage:
    """Customer journey stage definition."""
    name: str
    duration: str
    touchpoints: List[str]
    success_metrics: List[str]
    description: Optional[str] = None


class CustomerSegment(BaseModel):
    """Customer segment definition."""
    name: str
    properties: Dict[str, Any]
    constraints: List[str] = Field(default_factory=list)
    journey_stages: Dict[str, JourneyStage] = Field(default_factory=dict)
    description: Optional[str] = None
    
    @field_validator('properties')
    @classmethod
    def validate_properties(cls, v):
        """Validate that properties are well-formed."""
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError(f"Property name must be string, got {type(key)}")
        return v


class Campaign(BaseModel):
    """Marketing campaign definition."""
    name: str
    metadata: Dict[str, Any]
    components: Dict[str, Any]
    constraints: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class LeadScoringModel(BaseModel):
    """Lead scoring model definition."""
    name: str
    inputs: Dict[str, Any]
    output: Dict[str, Any]
    weights: Optional[Dict[str, float]] = None
    thresholds: Optional[Dict[str, int]] = None
    special_rules: List[str] = Field(default_factory=list)


class Ontology(BaseModel):
    """Main ontology container."""
    segments: Dict[str, CustomerSegment] = Field(default_factory=dict)
    campaigns: Dict[str, Campaign] = Field(default_factory=dict)
    lead_scoring: Optional[LeadScoringModel] = None
    types: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> Ontology:
        """Load ontology from YAML file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Ontology file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Transform the data to match the expected structure
        transformed_data = {}
        
        if "segments" in data:
            transformed_data["segments"] = {}
            for segment_name, segment_data in data["segments"].items():
                segment_data["name"] = segment_name
                
                # Transform journey stages to include name field
                if "journey_stages" in segment_data:
                    transformed_stages = {}
                    for stage_name, stage_data in segment_data["journey_stages"].items():
                        stage_data["name"] = stage_name
                        transformed_stages[stage_name] = stage_data
                    segment_data["journey_stages"] = transformed_stages
                
                transformed_data["segments"][segment_name] = segment_data
        
        if "campaigns" in data:
            transformed_data["campaigns"] = {}
            for campaign_name, campaign_data in data["campaigns"].items():
                campaign_data["name"] = campaign_name
                transformed_data["campaigns"][campaign_name] = campaign_data
        
        if "lead_scoring" in data:
            transformed_data["lead_scoring"] = data["lead_scoring"]
        
        if "types" in data:
            transformed_data["types"] = data["types"]
        
        return cls.model_validate(transformed_data)
    
    @classmethod
    def from_directory(cls, directory: Union[str, Path]) -> Ontology:
        """Load ontology from directory containing multiple YAML files."""
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Ontology directory not found: {directory}")
        
        ontology = cls()
        
        # Load all YAML files in the directory and subdirectories
        for yaml_file in directory.rglob("*.yaml"):
            try:
                file_ontology = cls.from_file(yaml_file)
                # Merge the ontologies
                ontology.segments.update(file_ontology.segments)
                ontology.campaigns.update(file_ontology.campaigns)
                ontology.types.update(file_ontology.types)
                if file_ontology.lead_scoring:
                    ontology.lead_scoring = file_ontology.lead_scoring
            except Exception as e:
                print(f"Warning: Failed to load {yaml_file}: {e}")
        
        return ontology
    
    def validate(self) -> List[str]:
        """Validate the ontology and return list of errors."""
        errors = []
        
        # Validate segments
        for segment_name, segment in self.segments.items():
            # Check for required properties
            if not segment.properties:
                errors.append(f"Segment {segment_name} has no properties")
            
            # Validate constraints
            for constraint in segment.constraints:
                if not isinstance(constraint, str):
                    errors.append(f"Segment {segment_name} has invalid constraint: {constraint}")
        
        # Validate campaigns
        for campaign_name, campaign in self.campaigns.items():
            if not campaign.metadata:
                errors.append(f"Campaign {campaign_name} has no metadata")
            
            if not campaign.components:
                errors.append(f"Campaign {campaign_name} has no components")
        
        # Validate lead scoring
        if self.lead_scoring:
            if not self.lead_scoring.inputs:
                errors.append("Lead scoring model has no inputs")
            
            if not self.lead_scoring.output:
                errors.append("Lead scoring model has no output")
        
        return errors
    
    def get_segment(self, name: str) -> Optional[CustomerSegment]:
        """Get a customer segment by name."""
        return self.segments.get(name)
    
    def get_campaign(self, name: str) -> Optional[Campaign]:
        """Get a campaign by name."""
        return self.campaigns.get(name)
    
    def list_segments(self) -> List[str]:
        """List all segment names."""
        return list(self.segments.keys())
    
    def list_campaigns(self) -> List[str]:
        """List all campaign names."""
        return list(self.campaigns.keys())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ontology to dictionary."""
        return self.model_dump()
    
    def save(self, file_path: Union[str, Path]) -> None:
        """Save ontology to YAML file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2) 