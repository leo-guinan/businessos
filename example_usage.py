#!/usr/bin/env python3
"""
Example usage of Business OS: Business-as-Code Platform

This script demonstrates how to:
1. Load and validate ontologies
2. Compile to different target formats
3. Use the generated schemas and models
"""

import json
from pathlib import Path
from businessos.core.ontology import Ontology
from businessos.core.validator import Validator
from businessos.core.compiler import Compiler


def main():
    """Main example function."""
    print("🚀 Business OS: Business-as-Code Platform Example")
    print("=" * 50)
    
    # Load ontology from the ontology directory
    ontology_dir = Path("ontology")
    if not ontology_dir.exists():
        print("❌ Ontology directory not found. Please run 'bos init' first.")
        return
    
    print("\n1. 📖 Loading Business Ontology...")
    try:
        ontology = Ontology.from_directory(ontology_dir)
        print(f"✅ Loaded ontology with {len(ontology.segments)} segments and {len(ontology.campaigns)} campaigns")
    except Exception as e:
        print(f"❌ Failed to load ontology: {e}")
        return
    
    # Validate the ontology
    print("\n2. 🔍 Validating Ontology...")
    validator = Validator(ontology)
    errors = validator.validate_all()
    
    if errors:
        print(f"⚠️  Found {len(errors)} validation issues:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"   - {error}")
        if len(errors) > 5:
            print(f"   ... and {len(errors) - 5} more")
    else:
        print("✅ Ontology is valid!")
    
    # List segments and campaigns
    print("\n3. 📋 Business Components:")
    segments = ontology.list_segments()
    campaigns = ontology.list_campaigns()
    
    print(f"   Customer Segments ({len(segments)}):")
    for segment in segments:
        print(f"     - {segment}")
    
    print(f"   Marketing Campaigns ({len(campaigns)}):")
    for campaign in campaigns:
        print(f"     - {campaign}")
    
    # Compile to different formats
    print("\n4. 🔧 Compiling to Target Formats...")
    compiler = Compiler(ontology)
    
    # Create output directory
    output_dir = Path("generated")
    output_dir.mkdir(exist_ok=True)
    
    # Compile to JSON Schema
    print("   📄 Generating JSON Schema...")
    schema = compiler.compile_to_json_schema()
    schema_file = output_dir / "business_schema.json"
    with open(schema_file, 'w') as f:
        json.dump(schema, f, indent=2)
    print(f"   ✅ JSON Schema saved to {schema_file}")
    
    # Compile to Pydantic models
    print("   🐍 Generating Pydantic Models...")
    pydantic_code = compiler.compile_to_pydantic()
    models_file = output_dir / "business_models.py"
    with open(models_file, 'w') as f:
        f.write(pydantic_code)
    print(f"   ✅ Pydantic models saved to {models_file}")
    
    # Compile to TypeScript interfaces
    print("   📘 Generating TypeScript Interfaces...")
    ts_code = compiler.compile_to_typescript()
    interfaces_file = output_dir / "business_interfaces.ts"
    with open(interfaces_file, 'w') as f:
        f.write(ts_code)
    print(f"   ✅ TypeScript interfaces saved to {interfaces_file}")
    
    # Demonstrate data validation
    print("\n5. ✅ Data Validation Example:")
    
    # Example customer data
    example_customer = {
        "company_size": "1000-5000",
        "industry": "technology",
        "annual_revenue": 50000000,
        "pain_points": ["scale", "integration"],
        "decision_makers": [
            {
                "title": "cto",
                "department": "engineering",
                "influence_level": "decision_maker",
                "technical_decision_maker": True,
                "budget_authority": True
            }
        ],
        "procurement_process": "rfi_rfp",
        "budget_cycle": "annual",
        "technical_maturity": "advanced"
    }
    
    # Validate against EnterpriseCustomer segment
    validation_errors = validator.validate_data_against_ontology(
        example_customer, "EnterpriseCustomer"
    )
    
    if validation_errors:
        print("   ❌ Validation failed:")
        for error in validation_errors:
            print(f"     - {error}")
    else:
        print("   ✅ Customer data is valid!")
    
    # Show business insights
    print("\n6. 💡 Business Insights:")
    
    # Analyze segments
    print("   Customer Segment Analysis:")
    for segment_name in segments:
        segment = ontology.get_segment(segment_name)
        if segment:
            prop_count = len(segment.properties)
            constraint_count = len(segment.constraints)
            print(f"     - {segment_name}: {prop_count} properties, {constraint_count} constraints")
    
    # Analyze campaigns
    print("   Marketing Campaign Analysis:")
    for campaign_name in campaigns:
        campaign = ontology.get_campaign(campaign_name)
        if campaign:
            owner_team = campaign.metadata.get("owner_team", "Unknown")
            campaign_type = campaign.metadata.get("campaign_type", "Unknown")
            component_count = len(campaign.components)
            print(f"     - {campaign_name}: {campaign_type} by {owner_team} ({component_count} components)")
    
    print("\n🎉 Business OS Example Complete!")
    print("\nNext steps:")
    print("1. Review generated files in the 'generated' directory")
    print("2. Use 'bos compile --target salesforce,hubspot' for CRM integration")
    print("3. Use 'bos train customer-classifier' to train ML models")
    print("4. Extend the ontology with your specific business rules")


if __name__ == "__main__":
    main() 