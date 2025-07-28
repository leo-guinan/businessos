"""
Business OS CLI tool.
"""

import typer
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core.ontology import Ontology
from .core.compiler import Compiler
from .core.validator import Validator

app = typer.Typer(help="Business OS: Business-as-Code Platform")
console = Console()


@app.command()
def init(
    project_name: str = typer.Argument(..., help="Name of the business project"),
    template: str = typer.Option("basic", help="Template to use for initialization")
):
    """Initialize a new Business OS project."""
    project_dir = Path(project_name)
    
    if project_dir.exists():
        console.print(f"[red]Error: Project directory '{project_name}' already exists[/red]")
        raise typer.Exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Initializing project...", total=None)
        
        # Create project structure
        project_dir.mkdir()
        (project_dir / "ontology").mkdir()
        (project_dir / "ontology" / "customers").mkdir()
        (project_dir / "ontology" / "products").mkdir()
        (project_dir / "ontology" / "marketing").mkdir()
        (project_dir / "ontology" / "sales").mkdir()
        (project_dir / "ontology" / "operations").mkdir()
        (project_dir / "generated").mkdir()
        (project_dir / "models").mkdir()
        (project_dir / "tests").mkdir()
        
        # Create initial ontology files
        _create_initial_ontologies(project_dir)
        
        progress.update(task, description="Project initialized successfully!")
    
    console.print(Panel(
        f"[green]Business OS project '{project_name}' created successfully![/green]\n\n"
        f"Next steps:\n"
        f"1. cd {project_name}\n"
        f"2. bos validate\n"
        f"3. bos compile --target json-schema,pydantic\n"
        f"4. Start defining your business ontology",
        title="🎉 Project Created"
    ))


@app.command()
def validate(
    ontology_path: str = typer.Argument("ontology", help="Path to ontology directory or file")
):
    """Validate Business OS ontology."""
    ontology_file = Path(ontology_path)
    
    if not ontology_file.exists():
        console.print(f"[red]Error: Ontology path '{ontology_path}' not found[/red]")
        raise typer.Exit(1)
    
    try:
        if ontology_file.is_file():
            ontology = Ontology.from_file(ontology_file)
        else:
            ontology = Ontology.from_directory(ontology_file)
        
        validator = Validator(ontology)
        errors = validator.validate_all()
        
        if not errors:
            console.print("[green]✅ Ontology is valid![/green]")
            return
        
        # Display errors
        table = Table(title="Validation Errors")
        table.add_column("Severity", style="red")
        table.add_column("Location")
        table.add_column("Message")
        
        for error in errors:
            severity_color = {
                "error": "red",
                "warning": "yellow", 
                "info": "blue"
            }.get(error.severity, "white")
            
            table.add_row(
                f"[{severity_color}]{error.severity.upper()}[/{severity_color}]",
                error.location or "unknown",
                error.message
            )
        
        console.print(table)
        
        summary = validator.get_validation_summary()
        if not summary["is_valid"]:
            raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[red]Error validating ontology: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def compile(
    ontology_path: str = typer.Argument("ontology", help="Path to ontology directory or file"),
    target: str = typer.Option(
        "json-schema", 
        "--target", "-t",
        help="Target formats to compile to (comma-separated)"
    ),
    output_dir: str = typer.Option(
        "generated",
        "--output", "-o", 
        help="Output directory for generated files"
    ),
    segment: Optional[str] = typer.Option(
        None,
        "--segment", "-s",
        help="Specific segment to compile (if not specified, compiles all)"
    )
):
    """Compile Business OS ontology to various target formats."""
    ontology_file = Path(ontology_path)
    output_path = Path(output_dir)
    
    if not ontology_file.exists():
        console.print(f"[red]Error: Ontology path '{ontology_path}' not found[/red]")
        raise typer.Exit(1)
    
    try:
        if ontology_file.is_file():
            ontology = Ontology.from_file(ontology_file)
        else:
            ontology = Ontology.from_directory(ontology_file)
        
        compiler = Compiler(ontology)
        
        # Parse target formats
        target_formats = [t.strip() for t in target.split(",")]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Compiling ontology...", total=len(target_formats))
            
            for target_format in target_formats:
                progress.update(task, description=f"Compiling to {target_format}...")
                
                if target_format == "json-schema":
                    schema = compiler.compile_to_json_schema(segment)
                    output_path.mkdir(parents=True, exist_ok=True)
                    schema_file = output_path / "schema.json"
                    import json
                    with open(schema_file, 'w') as f:
                        json.dump(schema, f, indent=2)
                
                elif target_format == "pydantic":
                    code = compiler.compile_to_pydantic(segment)
                    output_path.mkdir(parents=True, exist_ok=True)
                    model_file = output_path / "models.py"
                    with open(model_file, 'w') as f:
                        f.write(code)
                
                elif target_format == "typescript":
                    code = compiler.compile_to_typescript(segment)
                    output_path.mkdir(parents=True, exist_ok=True)
                    interface_file = output_path / "interfaces.ts"
                    with open(interface_file, 'w') as f:
                        f.write(code)
                
                elif target_format == "salesforce":
                    compiler.compile_to_salesforce(output_path / "salesforce")
                
                elif target_format == "hubspot":
                    compiler.compile_to_hubspot(output_path / "hubspot")
                
                elif target_format == "markdown":
                    compiler.compile_to_markdown(output_path / "markdown")
                
                else:
                    console.print(f"[yellow]Warning: Unknown target format '{target_format}'[/yellow]")
                
                progress.advance(task)
        
        console.print(f"[green]✅ Ontology compiled successfully to {output_dir}[/green]")
    
    except Exception as e:
        console.print(f"[red]Error compiling ontology: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_segments(
    ontology_path: str = typer.Argument("ontology", help="Path to ontology directory or file")
):
    """List all customer segments in the ontology."""
    ontology_file = Path(ontology_path)
    
    if not ontology_file.exists():
        console.print(f"[red]Error: Ontology path '{ontology_path}' not found[/red]")
        raise typer.Exit(1)
    
    try:
        if ontology_file.is_file():
            ontology = Ontology.from_file(ontology_file)
        else:
            ontology = Ontology.from_directory(ontology_file)
        
        segments = ontology.list_segments()
        
        if not segments:
            console.print("[yellow]No segments found in ontology[/yellow]")
            return
        
        table = Table(title="Customer Segments")
        table.add_column("Segment Name")
        table.add_column("Properties")
        table.add_column("Constraints")
        
        for segment_name in segments:
            segment = ontology.get_segment(segment_name)
            if segment:
                prop_count = len(segment.properties)
                constraint_count = len(segment.constraints)
                table.add_row(
                    segment_name,
                    str(prop_count),
                    str(constraint_count)
                )
        
        console.print(table)
    
    except Exception as e:
        console.print(f"[red]Error listing segments: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_campaigns(
    ontology_path: str = typer.Argument("ontology", help="Path to ontology directory or file")
):
    """List all marketing campaigns in the ontology."""
    ontology_file = Path(ontology_path)
    
    if not ontology_file.exists():
        console.print(f"[red]Error: Ontology path '{ontology_path}' not found[/red]")
        raise typer.Exit(1)
    
    try:
        if ontology_file.is_file():
            ontology = Ontology.from_file(ontology_file)
        else:
            ontology = Ontology.from_directory(ontology_file)
        
        campaigns = ontology.list_campaigns()
        
        if not campaigns:
            console.print("[yellow]No campaigns found in ontology[/yellow]")
            return
        
        table = Table(title="Marketing Campaigns")
        table.add_column("Campaign Name")
        table.add_column("Owner Team")
        table.add_column("Campaign Type")
        table.add_column("Components")
        
        for campaign_name in campaigns:
            campaign = ontology.get_campaign(campaign_name)
            if campaign:
                owner_team = campaign.metadata.get("owner_team", "Unknown")
                campaign_type = campaign.metadata.get("campaign_type", "Unknown")
                component_count = len(campaign.components)
                table.add_row(
                    campaign_name,
                    owner_team,
                    campaign_type,
                    str(component_count)
                )
        
        console.print(table)
    
    except Exception as e:
        console.print(f"[red]Error listing campaigns: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def add_segment(
    name: str = typer.Argument(..., help="Name of the segment to add"),
    ontology_path: str = typer.Option("ontology", help="Path to ontology directory"),
    company_size: Optional[str] = typer.Option(None, help="Company size range"),
    industry: Optional[str] = typer.Option(None, help="Industry type"),
    annual_revenue: Optional[str] = typer.Option(None, help="Annual revenue range")
):
    """Add a new customer segment to the ontology."""
    ontology_dir = Path(ontology_path)
    
    if not ontology_dir.exists():
        console.print(f"[red]Error: Ontology directory '{ontology_path}' not found[/red]")
        raise typer.Exit(1)
    
    # Create basic segment definition
    segment_data = {
        "properties": {}
    }
    
    if company_size:
        segment_data["properties"]["company_size"] = f'enum["{company_size}"]'
    
    if industry:
        segment_data["properties"]["industry"] = f'enum["{industry}"]'
    
    if annual_revenue:
        segment_data["properties"]["annual_revenue"] = f'range({annual_revenue})'
    
    # Add to segments file
    segments_file = ontology_dir / "customers" / "segments.yaml"
    
    if segments_file.exists():
        import yaml
        with open(segments_file, 'r') as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}
    
    if "segments" not in data:
        data["segments"] = {}
    
    data["segments"][name] = segment_data
    
    with open(segments_file, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, indent=2)
    
    console.print(f"[green]✅ Segment '{name}' added to ontology[/green]")


def _create_initial_ontologies(project_dir: Path):
    """Create initial ontology files for a new project."""
    import yaml
    
    # Create basic segments file
    segments_data = {
        "segments": {
            "EnterpriseCustomer": {
                "properties": {
                    "company_size": 'enum["1000-5000", "5000+"]',
                    "industry": 'enum["financial", "healthcare", "retail", "technology"]',
                    "annual_revenue": "range(10M, 1B+)"
                },
                "constraints": [
                    "Healthcare companies require HIPAA compliance",
                    "Financial companies require SOC2 Type II"
                ]
            }
        }
    }
    
    segments_file = project_dir / "ontology" / "customers" / "segments.yaml"
    with open(segments_file, 'w') as f:
        yaml.dump(segments_data, f, default_flow_style=False, indent=2)
    
    # Create basic campaigns file
    campaigns_data = {
        "campaigns": {
            "ProductLaunchCampaign": {
                "metadata": {
                    "owner_team": "product_marketing",
                    "campaign_type": "product_launch",
                    "target_audience": ["EnterpriseCustomer"]
                },
                "components": {
                    "announcement": {
                        "channels": ["blog", "email", "social"],
                        "success_metrics": ["reach", "engagement"]
                    }
                },
                "constraints": [
                    "All assets must follow brand guidelines"
                ]
            }
        }
    }
    
    campaigns_file = project_dir / "ontology" / "marketing" / "campaigns.yaml"
    with open(campaigns_file, 'w') as f:
        yaml.dump(campaigns_data, f, default_flow_style=False, indent=2)


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main() 