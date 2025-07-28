"""
Compiler for transforming Business OS ontologies into various target formats.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from jinja2 import Environment, FileSystemLoader, Template
from .ontology import Ontology


class Compiler:
    """Compiles Business OS ontologies into various target formats."""
    
    def __init__(self, ontology: Ontology):
        self.ontology = ontology
        self.env = Environment(loader=FileSystemLoader(self._get_template_dir()))
    
    def _get_template_dir(self) -> Path:
        """Get the template directory."""
        return Path(__file__).parent.parent / "templates"
    
    def compile_to_json_schema(self, segment_name: Optional[str] = None) -> Dict[str, Any]:
        """Compile ontology to JSON Schema."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {},
            "required": []
        }
        
        if segment_name:
            segment = self.ontology.get_segment(segment_name)
            if not segment:
                raise ValueError(f"Segment {segment_name} not found")
            
            schema["title"] = f"{segment_name} Schema"
            schema["properties"] = self._convert_properties_to_json_schema(segment.properties)
        else:
            # Compile all segments
            schema["title"] = "Business OS Ontology Schema"
            for name, segment in self.ontology.segments.items():
                schema["properties"][name] = {
                    "type": "object",
                    "title": name,
                    "properties": self._convert_properties_to_json_schema(segment.properties)
                }
        
        return schema
    
    def _convert_properties_to_json_schema(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ontology properties to JSON Schema format."""
        schema_properties = {}
        
        for prop_name, prop_def in properties.items():
            if isinstance(prop_def, str):
                # Simple type definition
                schema_properties[prop_name] = self._parse_type_definition(prop_def)
            elif isinstance(prop_def, dict):
                # Complex type definition
                schema_properties[prop_name] = self._parse_complex_type(prop_def)
            else:
                schema_properties[prop_name] = {"type": "string"}
        
        return schema_properties
    
    def _parse_type_definition(self, type_def: str) -> Dict[str, Any]:
        """Parse a type definition string into JSON Schema."""
        if type_def.startswith("enum["):
            # Parse enum type
            enum_values = type_def[5:-1].split(", ")
            return {
                "type": "string",
                "enum": enum_values
            }
        elif type_def.startswith("list["):
            # Parse list type
            inner_type = type_def[5:-1]
            return {
                "type": "array",
                "items": self._parse_type_definition(inner_type)
            }
        elif type_def.startswith("range("):
            # Parse range type
            range_def = type_def[6:-1]
            min_val, max_val = range_def.split(", ")
            
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
            
            return {
                "type": "number",
                "minimum": parse_value(min_val),
                "maximum": parse_value(max_val)
            }
        elif type_def == "boolean":
            return {"type": "boolean"}
        elif type_def == "int":
            return {"type": "integer"}
        elif type_def == "float":
            return {"type": "number"}
        elif type_def == "datetime":
            return {"type": "string", "format": "date-time"}
        else:
            return {"type": "string"}
    
    def _parse_complex_type(self, type_def: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a complex type definition."""
        # For now, treat as object with properties
        return {
            "type": "object",
            "properties": self._convert_properties_to_json_schema(type_def.get("properties", {}))
        }
    
    def compile_to_pydantic(self, segment_name: Optional[str] = None) -> str:
        """Compile ontology to Pydantic models."""
        template = self.env.get_template("pydantic_model.py.j2")
        
        if segment_name:
            segment = self.ontology.get_segment(segment_name)
            if not segment:
                raise ValueError(f"Segment {segment_name} not found")
            
            return template.render(
                segment_name=segment_name,
                properties=segment.properties,
                constraints=segment.constraints
            )
        else:
            return template.render(
                segments=self.ontology.segments,
                campaigns=self.ontology.campaigns,
                lead_scoring=self.ontology.lead_scoring,
                types=self.ontology.types
            )
    
    def compile_to_typescript(self, segment_name: Optional[str] = None) -> str:
        """Compile ontology to TypeScript interfaces."""
        template = self.env.get_template("typescript_interfaces.ts.j2")
        
        if segment_name:
            segment = self.ontology.get_segment(segment_name)
            if not segment:
                raise ValueError(f"Segment {segment_name} not found")
            
            return template.render(
                segment_name=segment_name,
                properties=segment.properties,
                constraints=segment.constraints
            )
        else:
            return template.render(
                segments=self.ontology.segments,
                campaigns=self.ontology.campaigns,
                lead_scoring=self.ontology.lead_scoring,
                types=self.ontology.types
            )
    
    def compile_to_salesforce(self, output_dir: Union[str, Path]) -> None:
        """Compile ontology to Salesforce metadata."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate custom objects
        for segment_name, segment in self.ontology.segments.items():
            self._generate_salesforce_object(segment_name, segment, output_dir)
        
        # Generate validation rules
        self._generate_salesforce_validation_rules(output_dir)
    
    def _generate_salesforce_object(self, segment_name: str, segment: Any, output_dir: Path) -> None:
        """Generate Salesforce custom object metadata."""
        template = self.env.get_template("salesforce_object.xml.j2")
        
        # Convert properties to Salesforce fields
        fields = []
        for prop_name, prop_def in segment.properties.items():
            field = self._convert_to_salesforce_field(prop_name, prop_def)
            fields.append(field)
        
        content = template.render(
            object_name=segment_name,
            fields=fields,
            description=segment.description or f"Custom object for {segment_name}"
        )
        
        # Write to file
        object_dir = output_dir / "objects" / segment_name
        object_dir.mkdir(parents=True, exist_ok=True)
        
        with open(object_dir / f"{segment_name}.object-meta.xml", 'w') as f:
            f.write(content)
    
    def _convert_to_salesforce_field(self, field_name: str, field_def: Any) -> Dict[str, Any]:
        """Convert ontology property to Salesforce field definition."""
        field = {
            "name": field_name,
            "label": field_name.replace("_", " ").title(),
            "type": "Text",
            "length": 255
        }
        
        if isinstance(field_def, str):
            if field_def.startswith("enum["):
                field["type"] = "Picklist"
                enum_values = field_def[5:-1].split(", ")
                field["values"] = enum_values
            elif field_def == "boolean":
                field["type"] = "Checkbox"
            elif field_def == "int":
                field["type"] = "Number"
                field["precision"] = 18
                field["scale"] = 0
            elif field_def == "float":
                field["type"] = "Number"
                field["precision"] = 18
                field["scale"] = 2
            elif field_def == "datetime":
                field["type"] = "DateTime"
        
        return field
    
    def _generate_salesforce_validation_rules(self, output_dir: Path) -> None:
        """Generate Salesforce validation rules from constraints."""
        template = self.env.get_template("salesforce_validation.xml.j2")
        
        for segment_name, segment in self.ontology.segments.items():
            if segment.constraints:
                content = template.render(
                    segment_name=segment_name,
                    constraints=segment.constraints
                )
                
                validation_dir = output_dir / "validationRules" / segment_name
                validation_dir.mkdir(parents=True, exist_ok=True)
                
                with open(validation_dir / f"{segment_name}_ValidationRule.validationRule-meta.xml", 'w') as f:
                    f.write(content)
    
    def compile_to_hubspot(self, output_dir: Union[str, Path]) -> None:
        """Compile ontology to HubSpot custom properties."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        template = self.env.get_template("hubspot_properties.json.j2")
        
        properties = []
        for segment_name, segment in self.ontology.segments.items():
            for prop_name, prop_def in segment.properties.items():
                property_def = self._convert_to_hubspot_property(prop_name, prop_def)
                properties.append(property_def)
        
        content = template.render(properties=properties)
        
        with open(output_dir / "custom_properties.json", 'w') as f:
            f.write(content)
    
    def _convert_to_hubspot_property(self, prop_name: str, prop_def: Any) -> Dict[str, Any]:
        """Convert ontology property to HubSpot property definition."""
        property_def = {
            "name": prop_name,
            "label": prop_name.replace("_", " ").title(),
            "type": "string",
            "groupName": "businessos"
        }
        
        if isinstance(prop_def, str):
            if prop_def.startswith("enum["):
                property_def["type"] = "enumeration"
                enum_values = prop_def[5:-1].split(", ")
                property_def["options"] = [{"label": val, "value": val} for val in enum_values]
            elif prop_def == "boolean":
                property_def["type"] = "boolean"
            elif prop_def == "int":
                property_def["type"] = "number"
            elif prop_def == "float":
                property_def["type"] = "number"
            elif prop_def == "datetime":
                property_def["type"] = "datetime"
        
        return property_def
    
    def compile_to_markdown(self, output_dir: Union[str, Path]) -> None:
        """Compile ontology to Markdown documentation."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate main documentation
        template = self.env.get_template("ontology_docs.md.j2")
        content = template.render(
            segments=self.ontology.segments,
            campaigns=self.ontology.campaigns,
            lead_scoring=self.ontology.lead_scoring
        )
        
        with open(output_dir / "ontology_documentation.md", 'w') as f:
            f.write(content)
        
        # Generate individual segment docs
        for segment_name, segment in self.ontology.segments.items():
            segment_template = self.env.get_template("segment_docs.md.j2")
            segment_content = segment_template.render(
                segment_name=segment_name,
                segment=segment
            )
            
            with open(output_dir / f"{segment_name}_documentation.md", 'w') as f:
                f.write(segment_content)
    
    def compile_all(self, output_dir: Union[str, Path], targets: List[str]) -> None:
        """Compile ontology to multiple target formats."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for target in targets:
            target_dir = output_dir / target
            target_dir.mkdir(exist_ok=True)
            
            if target == "json-schema":
                schema = self.compile_to_json_schema()
                with open(target_dir / "schema.json", 'w') as f:
                    json.dump(schema, f, indent=2)
            
            elif target == "pydantic":
                code = self.compile_to_pydantic()
                with open(target_dir / "models.py", 'w') as f:
                    f.write(code)
            
            elif target == "typescript":
                code = self.compile_to_typescript()
                with open(target_dir / "interfaces.ts", 'w') as f:
                    f.write(code)
            
            elif target == "salesforce":
                self.compile_to_salesforce(target_dir)
            
            elif target == "hubspot":
                self.compile_to_hubspot(target_dir)
            
            elif target == "markdown":
                self.compile_to_markdown(target_dir)
            
            else:
                print(f"Warning: Unknown target format '{target}'") 