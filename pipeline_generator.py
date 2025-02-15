"""
Module to generate a pipeline definition.
Loads an external configuration if available, or uses built-in templates.
Now includes an 'llm_hint' field for each stage and task when llm_hunt is enabled.
"""

import os
import yaml
import logging

from config import PIPELINE_CONFIG_FILE

logger = logging.getLogger(__name__)

def load_external_pipeline_config():
    """
    Load external pipeline configuration from a YAML file if it exists.
    """
    if os.path.isfile(PIPELINE_CONFIG_FILE):
        try:
            with open(PIPELINE_CONFIG_FILE, "r", encoding="utf8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Error loading pipeline config: {e}")
    return None

def generate_pipeline_definition(project_type, llm_hunt=False):
    """
    Generate an adaptive pipeline definition based on project type.
    For 'python_backend', defines backend stages.
    For 'frontend' and 'generic', stubs are provided.
    When llm_hunt is True, each stage/task includes a descriptive 'llm_hint'.
    """
    external_config = load_external_pipeline_config()
    if external_config:
        logger.info("Using external pipeline configuration.")
        return external_config

    if project_type == "python_backend":
        pipeline = {
            "pipeline": {
                "name": "Deconstructed_Backend_Pipeline",
                "description": (
                    "A modular, language-agnostic pipeline that deconstructs a backend code repository into granular tasks and stages. "
                    "Focus areas include configuration management, business logic extraction, data model definition, API endpoint mapping, and deployment. "
                    "Each task is versioned and includes explicit dependencies." +
                    (" Use the provided hints to guide an LLM in understanding and reassembling the code." if llm_hunt else "")
                ),
                "stages": [
                    {
                        "id": 1,
                        "name": "Environment_And_Infrastructure_Setup",
                        "version": "1.0",
                        "description": "Set up configuration management, logging, and dependency injection.",
                        "llm_hint": "This stage establishes the necessary foundation for the application, including managing configuration and logging." if llm_hunt else "",
                        "tasks": [
                            {
                                "id": "1.1",
                                "name": "Define_Configuration_Manager",
                                "version": "1.0",
                                "description": "Create a module to manage application configuration.",
                                "input": None,
                                "output": "Configuration_Manager",
                                "dependencies": [],
                                "llm_hint": "Ensure that all configuration variables are centralized and easily modifiable." if llm_hunt else ""
                            },
                            {
                                "id": "1.2",
                                "name": "Establish_Logging_Framework",
                                "version": "1.0",
                                "description": "Set up a logging system for tracking events and errors.",
                                "input": None,
                                "output": "Logging_Framework",
                                "dependencies": [],
                                "llm_hint": "Implement a logging mechanism that captures important events and errors throughout the system." if llm_hunt else ""
                            }
                        ],
                        "dependencies": []
                    },
                    {
                        "id": 2,
                        "name": "Core_Business_Logic_Extraction",
                        "version": "1.0",
                        "description": "Extract and modularize core business functions and data processing routines.",
                        "llm_hint": "This stage isolates the core algorithms and business logic for independent analysis and potential modification." if llm_hunt else "",
                        "tasks": [
                            {
                                "id": "2.1",
                                "name": "Extract_Service_Functions",
                                "version": "1.0",
                                "description": "Identify and encapsulate core business logic from the codebase.",
                                "input": "Source Code",
                                "output": "Business_Logic_Modules",
                                "dependencies": [],
                                "llm_hint": "Focus on the functions that implement key business rules and services." if llm_hunt else ""
                            },
                            {
                                "id": "2.2",
                                "name": "Define_Data_Models",
                                "version": "1.0",
                                "description": "Map database schemas and define ORM models.",
                                "input": "Business_Logic_Modules",
                                "output": "Data_Model_Definitions",
                                "dependencies": ["2.1"],
                                "llm_hint": "Identify and document the data structures and relationships used for persistence." if llm_hunt else ""
                            }
                        ],
                        "dependencies": [1]
                    },
                    {
                        "id": 3,
                        "name": "API_Endpoint_Definition_And_Testing",
                        "version": "1.0",
                        "description": "Expose business logic via API endpoints and validate functionality with tests.",
                        "llm_hint": "This stage bridges the business logic to external interfaces and ensures they work as expected." if llm_hunt else "",
                        "tasks": [
                            {
                                "id": "3.1",
                                "name": "Define_API_Routes",
                                "version": "1.0",
                                "description": "Map business logic modules to RESTful API endpoints.",
                                "input": "Business_Logic_Modules",
                                "output": "API_Routes",
                                "dependencies": ["2.1"],
                                "llm_hint": "Design clear and maintainable API endpoints that accurately reflect the underlying business operations." if llm_hunt else ""
                            },
                            {
                                "id": "3.2",
                                "name": "Integration_Testing",
                                "version": "1.0",
                                "description": "Develop integration tests for API endpoints.",
                                "input": "API_Routes",
                                "output": "Test_Reports",
                                "dependencies": ["3.1"],
                                "llm_hint": "Ensure that the endpoints function correctly and that the business logic integrates seamlessly with the API." if llm_hunt else ""
                            }
                        ],
                        "dependencies": [2]
                    },
                    {
                        "id": 4,
                        "name": "Build_And_Deployment",
                        "version": "1.0",
                        "description": "Package the application and automate deployment processes.",
                        "llm_hint": "This final stage focuses on turning the modular components into a deployable system." if llm_hunt else "",
                        "tasks": [
                            {
                                "id": "4.1",
                                "name": "Define_Build_Scripts",
                                "version": "1.0",
                                "description": "Create build scripts (e.g., Dockerfiles) to assemble the application.",
                                "input": "Modular Outputs",
                                "output": "Build_Scripts",
                                "dependencies": [],
                                "llm_hint": "Generate scripts that package the application reliably across environments." if llm_hunt else ""
                            },
                            {
                                "id": "4.2",
                                "name": "Automate_CI_CD",
                                "version": "1.0",
                                "description": "Set up CI/CD pipelines for testing and deployment.",
                                "input": "Build_Scripts",
                                "output": "CI_CD_Configuration",
                                "dependencies": ["4.1"],
                                "llm_hint": "Implement automation for testing and deployment to ensure rapid and reliable delivery." if llm_hunt else ""
                            }
                        ],
                        "dependencies": [1, 2, 3]
                    }
                ],
                "overall_dependencies": [
                    "Stage 1 provides the infrastructure foundation.",
                    "Stage 2 extracts and modularizes core business logic.",
                    "Stage 3 maps logic to API endpoints and validates functionality.",
                    "Stage 4 packages and deploys the backend application."
                ]
            }
        }
    elif project_type == "frontend":
        pipeline = {
            "pipeline": {
                "name": "Deconstructed_Frontend_Pipeline",
                "description": (
                    "A modular pipeline that deconstructs a frontend code repository into tasks focused on UI rendering, "
                    "client-side interactions, and dynamic content updates." +
                    (" Use hints to guide the LLM in understanding UI design choices." if llm_hunt else "")
                ),
                "stages": [
                    # Frontend-specific stages would be defined here.
                ],
                "overall_dependencies": [
                    "Front-end modules depend on robust UI rendering and dynamic updates."
                ]
            }
        }
    else:
        pipeline = {
            "pipeline": {
                "name": "Deconstructed_Code_Repository_Pipeline",
                "description": (
                    "A generic modular pipeline that deconstructs a code repository into granular tasks and stages. "
                    "It is intended to be customized based on project-specific needs." +
                    (" Hints may help guide LLM reassembly." if llm_hunt else "")
                ),
                "stages": [],
                "overall_dependencies": [
                    "This pipeline is a generic template to be customized as needed."
                ]
            }
        }
    return pipeline
