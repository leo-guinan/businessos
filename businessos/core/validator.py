"""
Validator for Business OS ontologies.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from .ontology import Ontology


class ValidationError:
    """Represents a validation error."""
    
    def __init__(self, message: str, severity: str = "error", location: Optional[str] = None):
        self.message = message
        self.severity = severity  # error, warning, info
        self.location = location
    
    def __str__(self) -> str:
        location_str = f" at {self.location}" if self.location else ""
        return f"{self.severity.upper()}{location_str}: {self.message}"


class Validator:
    """Validates Business OS ontologies for consistency and business rules."""
    
    def __init__(self, ontology: Ontology):
        self.ontology = ontology
        self.errors: List[ValidationError] = []
    
    def validate_all(self) -> List[ValidationError]:
        """Run all validation checks."""
        self.errors = []
        
        self._validate_segments()
        self._validate_campaigns()
        self._validate_lead_scoring()
        self._validate_types()
        self._validate_constraints()
        self._validate_journey_stages()
        
        return self.errors
    
    def _validate_segments(self) -> None:
        """Validate customer segments."""
        for segment_name, segment in self.ontology.segments.items():
            # Check segment name format
            if not re.match(r'^[A-Z][a-zA-Z0-9_]*$', segment_name):
                self.errors.append(ValidationError(
                    f"Segment name '{segment_name}' should be PascalCase",
                    location=f"segments.{segment_name}"
                ))
            
            # Check properties
            if not segment.properties:
                self.errors.append(ValidationError(
                    f"Segment '{segment_name}' has no properties",
                    location=f"segments.{segment_name}"
                ))
            
            # Validate each property
            for prop_name, prop_def in segment.properties.items():
                self._validate_property(prop_name, prop_def, f"segments.{segment_name}")
    
    def _validate_campaigns(self) -> None:
        """Validate marketing campaigns."""
        for campaign_name, campaign in self.ontology.campaigns.items():
            # Check campaign name format
            if not re.match(r'^[A-Z][a-zA-Z0-9_]*$', campaign_name):
                self.errors.append(ValidationError(
                    f"Campaign name '{campaign_name}' should be PascalCase",
                    location=f"campaigns.{campaign_name}"
                ))
            
            # Check required metadata
            required_metadata = ["owner_team", "campaign_type", "target_audience"]
            for field in required_metadata:
                if field not in campaign.metadata:
                    self.errors.append(ValidationError(
                        f"Campaign '{campaign_name}' missing required metadata: {field}",
                        location=f"campaigns.{campaign_name}.metadata"
                    ))
            
            # Check components
            if not campaign.components:
                self.errors.append(ValidationError(
                    f"Campaign '{campaign_name}' has no components",
                    location=f"campaigns.{campaign_name}"
                ))
    
    def _validate_lead_scoring(self) -> None:
        """Validate lead scoring model."""
        if not self.ontology.lead_scoring:
            return
        
        scoring = self.ontology.lead_scoring
        
        # Check inputs
        if not scoring.inputs:
            self.errors.append(ValidationError(
                "Lead scoring model has no inputs",
                location="lead_scoring"
            ))
        
        # Check output
        if not scoring.output:
            self.errors.append(ValidationError(
                "Lead scoring model has no output",
                location="lead_scoring"
            ))
        
        # Validate score range
        if "score" in scoring.output:
            score_def = scoring.output["score"]
            if isinstance(score_def, str) and "int(0, 100)" not in score_def:
                self.errors.append(ValidationError(
                    "Lead score should be int(0, 100)",
                    location="lead_scoring.output.score"
                ))
    
    def _validate_types(self) -> None:
        """Validate type definitions."""
        for type_name, type_def in self.ontology.types.items():
            # Check type name format
            if not re.match(r'^[A-Z][a-zA-Z0-9_]*$', type_name):
                self.errors.append(ValidationError(
                    f"Type name '{type_name}' should be PascalCase",
                    location=f"types.{type_name}"
                ))
            
            # Check properties
            if isinstance(type_def, dict) and "properties" in type_def:
                for prop_name, prop_def in type_def["properties"].items():
                    self._validate_property(prop_name, prop_def, f"types.{type_name}")
    
    def _validate_property(self, prop_name: str, prop_def: Any, location: str) -> None:
        """Validate a property definition."""
        # Check property name format
        if not re.match(r'^[a-z][a-zA-Z0-9_]*$', prop_name):
            self.errors.append(ValidationError(
                f"Property name '{prop_name}' should be camelCase",
                location=f"{location}.{prop_name}"
            ))
        
        # Validate type definition
        if isinstance(prop_def, str):
            self._validate_type_definition(prop_def, f"{location}.{prop_name}")
        elif isinstance(prop_def, dict):
            self._validate_complex_property(prop_def, f"{location}.{prop_name}")
    
    def _validate_type_definition(self, type_def: str, location: str) -> None:
        """Validate a type definition string."""
        # Check enum format
        if type_def.startswith("enum["):
            if not type_def.endswith("]"):
                self.errors.append(ValidationError(
                    f"Invalid enum definition: {type_def}",
                    location=location
                ))
            else:
                enum_content = type_def[5:-1]
                # Check if values are properly quoted
                if not all(val.strip().startswith('"') and val.strip().endswith('"') for val in enum_content.split(", ")):
                    self.errors.append(ValidationError(
                        f"Enum values must be quoted: {type_def}",
                        location=location
                    ))
                else:
                    enum_values = enum_content.split(", ")
                    if not enum_values or not all(enum_values):
                        self.errors.append(ValidationError(
                            f"Enum must have at least one value: {type_def}",
                            location=location
                        ))
        
        # Check list format
        elif type_def.startswith("list["):
            if not type_def.endswith("]"):
                self.errors.append(ValidationError(
                    f"Invalid list definition: {type_def}",
                    location=location
                ))
            else:
                inner_type = type_def[5:-1]
                if not inner_type:
                    self.errors.append(ValidationError(
                        f"List must specify inner type: {type_def}",
                        location=location
                    ))
        
        # Check range format
        elif type_def.startswith("range("):
            if not type_def.endswith(")"):
                self.errors.append(ValidationError(
                    f"Invalid range definition: {type_def}",
                    location=location
                ))
            else:
                range_def = type_def[6:-1]
                parts = range_def.split(", ")
                if len(parts) != 2:
                    self.errors.append(ValidationError(
                        f"Range must have min and max values: {type_def}",
                        location=location
                    ))
        
        # Check basic types
        elif type_def not in ["string", "int", "float", "boolean", "datetime"]:
            self.errors.append(ValidationError(
                f"Unknown type: {type_def}",
                location=location
            ))
    
    def _validate_complex_property(self, prop_def: Dict[str, Any], location: str) -> None:
        """Validate a complex property definition."""
        if "properties" not in prop_def:
            self.errors.append(ValidationError(
                f"Complex property must have 'properties' field",
                location=location
            ))
        else:
            for prop_name, prop_type in prop_def["properties"].items():
                self._validate_property(prop_name, prop_type, f"{location}.properties")
    
    def _validate_constraints(self) -> None:
        """Validate business constraints."""
        for segment_name, segment in self.ontology.segments.items():
            for i, constraint in enumerate(segment.constraints):
                if not isinstance(constraint, str):
                    self.errors.append(ValidationError(
                        f"Constraint must be a string",
                        location=f"segments.{segment_name}.constraints[{i}]"
                    ))
                elif len(constraint.strip()) == 0:
                    self.errors.append(ValidationError(
                        f"Constraint cannot be empty",
                        location=f"segments.{segment_name}.constraints[{i}]"
                    ))
    
    def _validate_journey_stages(self) -> None:
        """Validate customer journey stages."""
        for segment_name, segment in self.ontology.segments.items():
            if hasattr(segment, 'journey_stages'):
                for stage_name, stage in segment.journey_stages.items():
                    # Check stage name format
                    if not re.match(r'^[a-z][a-zA-Z0-9_]*$', stage_name):
                        self.errors.append(ValidationError(
                            f"Journey stage name '{stage_name}' should be camelCase",
                            location=f"segments.{segment_name}.journey_stages.{stage_name}"
                        ))
                    
                    # Check required fields
                    required_fields = ["duration", "touchpoints", "success_metrics"]
                    for field in required_fields:
                        if not hasattr(stage, field) or not getattr(stage, field):
                            self.errors.append(ValidationError(
                                f"Journey stage '{stage_name}' missing required field: {field}",
                                location=f"segments.{segment_name}.journey_stages.{stage_name}"
                            ))
    
    def validate_data_against_ontology(self, data: Dict[str, Any], segment_name: str) -> List[ValidationError]:
        """Validate data against a specific segment's ontology."""
        errors = []
        segment = self.ontology.get_segment(segment_name)
        
        if not segment:
            errors.append(ValidationError(f"Segment '{segment_name}' not found"))
            return errors
        
        # Check required properties
        for prop_name, prop_def in segment.properties.items():
            if prop_name not in data:
                errors.append(ValidationError(
                    f"Missing required property: {prop_name}",
                    location=f"data.{segment_name}"
                ))
                continue
            
            # Validate property value
            value = data[prop_name]
            validation_error = self._validate_value_against_type(value, prop_def, prop_name)
            if validation_error:
                errors.append(validation_error)
        
        # Check for extra properties
        for prop_name in data:
            if prop_name not in segment.properties:
                errors.append(ValidationError(
                    f"Unknown property: {prop_name}",
                    location=f"data.{segment_name}",
                    severity="warning"
                ))
        
        return errors
    
    def _validate_value_against_type(self, value: Any, type_def: Any, prop_name: str) -> Optional[ValidationError]:
        """Validate a value against its type definition."""
        if isinstance(type_def, str):
            return self._validate_value_against_simple_type(value, type_def, prop_name)
        elif isinstance(type_def, dict):
            return self._validate_value_against_complex_type(value, type_def, prop_name)
        return None
    
    def _validate_value_against_simple_type(self, value: Any, type_def: str, prop_name: str) -> Optional[ValidationError]:
        """Validate a value against a simple type definition."""
        if type_def.startswith("enum["):
            enum_content = type_def[5:-1]
            enum_values = [val.strip().strip('"') for val in enum_content.split(", ")]
            if value not in enum_values:
                return ValidationError(
                    f"Value '{value}' not in enum {enum_values}",
                    location=f"data.{prop_name}"
                )
        
        elif type_def.startswith("list["):
            if not isinstance(value, list):
                return ValidationError(
                    f"Value must be a list for type {type_def}",
                    location=f"data.{prop_name}"
                )
            
            inner_type = type_def[5:-1]
            for i, item in enumerate(value):
                item_error = self._validate_value_against_simple_type(item, inner_type, f"{prop_name}[{i}]")
                if item_error:
                    return item_error
        
        elif type_def.startswith("range("):
            range_def = type_def[6:-1]
            min_val, max_val = range_def.split(", ")
            try:
                num_value = float(value)
                
                # Handle units like K, M, B
                def parse_value(val):
                    val = val.strip()
                    if val.endswith('K'):
                        return float(val[:-1]) * 1000
                    elif val.endswith('M'):
                        return float(val[:-1]) * 1000000
                    elif val.endswith('B'):
                        return float(val[:-1]) * 1000000000
                    elif val.endswith('+'):
                        return float(val[:-1])
                    else:
                        return float(val)
                
                min_num = parse_value(min_val)
                max_num = parse_value(max_val)
                if not (min_num <= num_value <= max_num):
                    return ValidationError(
                        f"Value {value} not in range [{min_val}, {max_val}]",
                        location=f"data.{prop_name}"
                    )
            except (ValueError, TypeError):
                return ValidationError(
                    f"Value must be numeric for range type",
                    location=f"data.{prop_name}"
                )
        
        elif type_def == "boolean" and not isinstance(value, bool):
            return ValidationError(
                f"Value must be boolean for type {type_def}",
                location=f"data.{prop_name}"
            )
        
        elif type_def == "int":
            try:
                int(value)
            except (ValueError, TypeError):
                return ValidationError(
                    f"Value must be integer for type {type_def}",
                    location=f"data.{prop_name}"
                )
        
        elif type_def == "float":
            try:
                float(value)
            except (ValueError, TypeError):
                return ValidationError(
                    f"Value must be numeric for type {type_def}",
                    location=f"data.{prop_name}"
                )
        
        return None
    
    def _validate_value_against_complex_type(self, value: Any, type_def: Dict[str, Any], prop_name: str) -> Optional[ValidationError]:
        """Validate a value against a complex type definition."""
        if not isinstance(value, dict):
            return ValidationError(
                f"Value must be an object for complex type",
                location=f"data.{prop_name}"
            )
        
        if "properties" in type_def:
            for sub_prop_name, sub_prop_def in type_def["properties"].items():
                if sub_prop_name in value:
                    sub_error = self._validate_value_against_type(
                        value[sub_prop_name], 
                        sub_prop_def, 
                        f"{prop_name}.{sub_prop_name}"
                    )
                    if sub_error:
                        return sub_error
        
        return None
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of validation results."""
        error_count = len([e for e in self.errors if e.severity == "error"])
        warning_count = len([e for e in self.errors if e.severity == "warning"])
        info_count = len([e for e in self.errors if e.severity == "info"])
        
        return {
            "total_errors": len(self.errors),
            "errors": error_count,
            "warnings": warning_count,
            "info": info_count,
            "is_valid": error_count == 0
        } 