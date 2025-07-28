"""
Tests for Business OS ontology functionality.
"""

import pytest
from pathlib import Path
from businessos.core.ontology import Ontology
from businessos.core.validator import Validator, ValidationError


class TestOntology:
    """Test ontology loading and parsing."""
    
    def test_load_ontology_from_file(self, tmp_path):
        """Test loading ontology from a single file."""
        # Create a test ontology file
        ontology_data = {
            "segments": {
                "TestCustomer": {
                    "properties": {
                        "company_size": 'enum["1-10", "11-50"]',
                        "industry": 'enum["technology", "healthcare"]',
                        "annual_revenue": "range(100K, 10M)"
                    },
                    "constraints": [
                        "Technology companies must have technical decision maker"
                    ]
                }
            }
        }
        
        import yaml
        ontology_file = tmp_path / "test_ontology.yaml"
        with open(ontology_file, 'w') as f:
            yaml.dump(ontology_data, f)
        
        # Load ontology
        ontology = Ontology.from_file(ontology_file)
        
        assert "TestCustomer" in ontology.segments
        assert len(ontology.segments) == 1
        
        segment = ontology.segments["TestCustomer"]
        assert "company_size" in segment.properties
        assert "industry" in segment.properties
        assert "annual_revenue" in segment.properties
        assert len(segment.constraints) == 1
    
    def test_load_ontology_from_directory(self, tmp_path):
        """Test loading ontology from a directory with multiple files."""
        # Create ontology directory structure
        ontology_dir = tmp_path / "ontology"
        ontology_dir.mkdir()
        
        # Create segments file
        segments_data = {
            "segments": {
                "EnterpriseCustomer": {
                    "properties": {
                        "company_size": 'enum["1000-5000", "5000+"]',
                        "industry": 'enum["financial", "healthcare"]'
                    }
                }
            }
        }
        
        # Create campaigns file
        campaigns_data = {
            "campaigns": {
                "ProductLaunchCampaign": {
                    "metadata": {
                        "owner_team": "product_marketing",
                        "campaign_type": "product_launch"
                    },
                    "components": {
                        "announcement": {
                            "channels": ["blog", "email"]
                        }
                    }
                }
            }
        }
        
        import yaml
        segments_file = ontology_dir / "segments.yaml"
        campaigns_file = ontology_dir / "campaigns.yaml"
        
        with open(segments_file, 'w') as f:
            yaml.dump(segments_data, f)
        
        with open(campaigns_file, 'w') as f:
            yaml.dump(campaigns_data, f)
        
        # Load ontology
        ontology = Ontology.from_directory(ontology_dir)
        
        assert "EnterpriseCustomer" in ontology.segments
        assert "ProductLaunchCampaign" in ontology.campaigns
        assert len(ontology.segments) == 1
        assert len(ontology.campaigns) == 1
    
    def test_get_segment(self, tmp_path):
        """Test getting a specific segment by name."""
        ontology_data = {
            "segments": {
                "TestCustomer": {
                    "properties": {
                        "company_size": 'enum["1-10", "11-50"]'
                    }
                }
            }
        }
        
        import yaml
        ontology_file = tmp_path / "test_ontology.yaml"
        with open(ontology_file, 'w') as f:
            yaml.dump(ontology_data, f)
        
        ontology = Ontology.from_file(ontology_file)
        
        segment = ontology.get_segment("TestCustomer")
        assert segment is not None
        assert "company_size" in segment.properties
        
        # Test non-existent segment
        segment = ontology.get_segment("NonExistent")
        assert segment is None
    
    def test_list_segments(self, tmp_path):
        """Test listing all segment names."""
        ontology_data = {
            "segments": {
                "Customer1": {"properties": {}},
                "Customer2": {"properties": {}},
                "Customer3": {"properties": {}}
            }
        }
        
        import yaml
        ontology_file = tmp_path / "test_ontology.yaml"
        with open(ontology_file, 'w') as f:
            yaml.dump(ontology_data, f)
        
        ontology = Ontology.from_file(ontology_file)
        segments = ontology.list_segments()
        
        assert len(segments) == 3
        assert "Customer1" in segments
        assert "Customer2" in segments
        assert "Customer3" in segments


class TestValidator:
    """Test ontology validation."""
    
    def test_validate_valid_ontology(self, tmp_path):
        """Test validation of a valid ontology."""
        ontology_data = {
            "segments": {
                "ValidCustomer": {
                    "properties": {
                        "company_size": 'enum["1-10", "11-50"]',
                        "industry": 'enum["technology"]'
                    },
                    "constraints": [
                        "Valid constraint"
                    ]
                }
            }
        }
        
        import yaml
        ontology_file = tmp_path / "valid_ontology.yaml"
        with open(ontology_file, 'w') as f:
            yaml.dump(ontology_data, f)
        
        ontology = Ontology.from_file(ontology_file)
        validator = Validator(ontology)
        errors = validator.validate_all()
        
        assert len(errors) == 0
    
    def test_validate_invalid_segment_name(self, tmp_path):
        """Test validation with invalid segment name format."""
        ontology_data = {
            "segments": {
                "invalid-name": {  # Invalid: should be PascalCase
                    "properties": {
                        "company_size": 'enum["1-10", "11-50"]'
                    }
                }
            }
        }
        
        import yaml
        ontology_file = tmp_path / "invalid_ontology.yaml"
        with open(ontology_file, 'w') as f:
            yaml.dump(ontology_data, f)
        
        ontology = Ontology.from_file(ontology_file)
        validator = Validator(ontology)
        errors = validator.validate_all()
        
        assert len(errors) > 0
        assert any("should be PascalCase" in str(error) for error in errors)
    
    def test_validate_invalid_property_name(self, tmp_path):
        """Test validation with invalid property name format."""
        ontology_data = {
            "segments": {
                "ValidCustomer": {
                    "properties": {
                        "Invalid-Property": 'enum["1-10", "11-50"]'  # Invalid: should be camelCase
                    }
                }
            }
        }
        
        import yaml
        ontology_file = tmp_path / "invalid_ontology.yaml"
        with open(ontology_file, 'w') as f:
            yaml.dump(ontology_data, f)
        
        ontology = Ontology.from_file(ontology_file)
        validator = Validator(ontology)
        errors = validator.validate_all()
        
        assert len(errors) > 0
        assert any("should be camelCase" in str(error) for error in errors)
    
    def test_validate_invalid_enum_definition(self, tmp_path):
        """Test validation with invalid enum definition."""
        ontology_data = {
            "segments": {
                "ValidCustomer": {
                    "properties": {
                        "company_size": 'enum[1-10, 11-50]'  # Invalid: missing quotes
                    }
                }
            }
        }
        
        import yaml
        ontology_file = tmp_path / "invalid_ontology.yaml"
        with open(ontology_file, 'w') as f:
            yaml.dump(ontology_data, f)
        
        ontology = Ontology.from_file(ontology_file)
        validator = Validator(ontology)
        errors = validator.validate_all()
        
        assert len(errors) > 0
    
    def test_validate_data_against_ontology(self, tmp_path):
        """Test validating data against ontology."""
        ontology_data = {
            "segments": {
                "TestCustomer": {
                    "properties": {
                        "company_size": 'enum["1-10", "11-50"]',
                        "industry": 'enum["technology", "healthcare"]',
                        "annual_revenue": "range(100K, 10M)"
                    }
                }
            }
        }
        
        import yaml
        ontology_file = tmp_path / "test_ontology.yaml"
        with open(ontology_file, 'w') as f:
            yaml.dump(ontology_data, f)
        
        ontology = Ontology.from_file(ontology_file)
        validator = Validator(ontology)
        
        # Valid data
        valid_data = {
            "company_size": "1-10",
            "industry": "technology",
            "annual_revenue": 500000
        }
        
        errors = validator.validate_data_against_ontology(valid_data, "TestCustomer")
        assert len(errors) == 0
        
        # Invalid data - wrong enum value
        invalid_data = {
            "company_size": "invalid-size",
            "industry": "technology",
            "annual_revenue": 500000
        }
        
        errors = validator.validate_data_against_ontology(invalid_data, "TestCustomer")
        assert len(errors) > 0
        assert any("not in enum" in str(error) for error in errors)
    
    def test_validation_summary(self, tmp_path):
        """Test validation summary generation."""
        ontology_data = {
            "segments": {
                "ValidCustomer": {
                    "properties": {
                        "company_size": 'enum["1-10", "11-50"]'
                    }
                },
                "invalid-customer": {  # Invalid name
                    "properties": {
                        "company_size": 'enum["1-10", "11-50"]'
                    }
                }
            }
        }
        
        import yaml
        ontology_file = tmp_path / "test_ontology.yaml"
        with open(ontology_file, 'w') as f:
            yaml.dump(ontology_data, f)
        
        ontology = Ontology.from_file(ontology_file)
        validator = Validator(ontology)
        validator.validate_all()
        
        summary = validator.get_validation_summary()
        
        assert summary["total_errors"] > 0
        assert summary["errors"] > 0
        assert not summary["is_valid"]


class TestCompiler:
    """Test ontology compilation."""
    
    def test_compile_to_json_schema(self, tmp_path):
        """Test compilation to JSON Schema."""
        ontology_data = {
            "segments": {
                "TestCustomer": {
                    "properties": {
                        "company_size": 'enum["1-10", "11-50"]',
                        "industry": 'enum["technology", "healthcare"]',
                        "annual_revenue": "range(100K, 10M)"
                    }
                }
            }
        }
        
        import yaml
        ontology_file = tmp_path / "test_ontology.yaml"
        with open(ontology_file, 'w') as f:
            yaml.dump(ontology_data, f)
        
        ontology = Ontology.from_file(ontology_file)
        from businessos.core.compiler import Compiler
        compiler = Compiler(ontology)
        
        schema = compiler.compile_to_json_schema()
        
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert "TestCustomer" in schema["properties"]
        
        customer_schema = schema["properties"]["TestCustomer"]
        assert customer_schema["type"] == "object"
        assert "company_size" in customer_schema["properties"]
        assert "industry" in customer_schema["properties"]
        assert "annual_revenue" in customer_schema["properties"]
    
    def test_compile_specific_segment(self, tmp_path):
        """Test compilation of a specific segment."""
        ontology_data = {
            "segments": {
                "TestCustomer": {
                    "properties": {
                        "company_size": 'enum["1-10", "11-50"]'
                    }
                }
            }
        }
        
        import yaml
        ontology_file = tmp_path / "test_ontology.yaml"
        with open(ontology_file, 'w') as f:
            yaml.dump(ontology_data, f)
        
        ontology = Ontology.from_file(ontology_file)
        from businessos.core.compiler import Compiler
        compiler = Compiler(ontology)
        
        schema = compiler.compile_to_json_schema("TestCustomer")
        
        assert schema["title"] == "TestCustomer Schema"
        assert "company_size" in schema["properties"]
    
    def test_compile_nonexistent_segment(self, tmp_path):
        """Test compilation of non-existent segment."""
        ontology_data = {
            "segments": {
                "TestCustomer": {
                    "properties": {
                        "company_size": 'enum["1-10", "11-50"]'
                    }
                }
            }
        }
        
        import yaml
        ontology_file = tmp_path / "test_ontology.yaml"
        with open(ontology_file, 'w') as f:
            yaml.dump(ontology_data, f)
        
        ontology = Ontology.from_file(ontology_file)
        from businessos.core.compiler import Compiler
        compiler = Compiler(ontology)
        
        with pytest.raises(ValueError, match="Segment NonExistent not found"):
            compiler.compile_to_json_schema("NonExistent") 