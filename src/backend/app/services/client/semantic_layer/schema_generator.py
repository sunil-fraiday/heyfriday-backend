import yaml
from typing import Dict, List

from app.core.config import settings
from app.utils.logger import get_logger
from app.models.mongodb.client_data_store import ClientDataStore
from app.services.client.data_store.data_store import ClientDataStoreService
from app.models.mongodb.utils import CredentialManager
from app.models.mongodb.enums import EngineType, DatabaseType

logger = get_logger(__name__)


class SchemaGenerator:
    """Generate Cube.js schema files from database metadata"""

    def __init__(self, data_store: ClientDataStore):
        self.data_store = data_store
        credential_manager = CredentialManager(current_key=settings.ENCRYPTION_KEY)
        self.store_service = ClientDataStoreService(credential_manager=credential_manager)
        self.service = self.store_service.get_service(data_store.client.client_id, data_store.database_type)
        self.config = credential_manager.decrypt_config(data_store.config)

    def get_tables(self) -> List[str]:
        """Get list of tables"""
        try:
            if self.data_store.database_type == DatabaseType.POSTGRES:
                query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """
            elif self.data_store.database_type == DatabaseType.CLICKHOUSE:
                query = "SHOW TABLES"
            else:
                raise ValueError(f"Unsupported engine type: {self.data_store.database_type}")

            result = self.service.raw_execute(self.config, query)
            return [table[0] for table in result]

        except Exception as e:
            logger.error(f"Error getting tables for {self.data_store.database_type}", exc_info=True)
            raise

    def get_columns(self, table: str) -> List[Dict]:
        """Get column information for a table"""
        try:
            if self.data_store.database_type == DatabaseType.POSTGRES:
                query = """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        CASE 
                            WHEN pk.contype = 'p' THEN true
                            ELSE false
                        END as is_primary
                    FROM information_schema.columns c
                    LEFT JOIN (
                        SELECT ka.attname, i.indisprimary, tc.contype
                        FROM pg_index i
                        JOIN pg_attribute ka ON ka.attrelid = i.indrelid 
                            AND ka.attnum = ANY(i.indkey)
                        JOIN pg_constraint tc ON tc.conrelid = i.indrelid 
                            AND tc.contype = 'p'
                        WHERE i.indisprimary
                    ) pk ON pk.attname = c.column_name
                    WHERE table_name = %(table)s
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                """
                result = self.service.raw_execute(self.config, query, {"table": table})
                return [
                    {
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                        "default": row[3],
                        "primary_key": row[4],
                    }
                    for row in result
                ]
            elif self.data_store.database_type == DatabaseType.CLICKHOUSE:
                result = self.service.raw_execute(self.config, f"DESCRIBE TABLE {table}")
                return [
                    {
                        "name": row[0],
                        "type": row[1],
                        "nullable": "Nullable" in row[1],
                        "default": row[3],
                        "primary_key": False,
                    }
                    for row in result
                ]
            else:
                raise ValueError(f"Unsupported engine type: {self.data_store.database_type}")

        except Exception as e:
            logger.error(f"Error getting columns for table {table}", exc_info=True)
            raise

    def map_type(self, db_type: str) -> str:
        """Map database types to Cube.js types"""
        numeric_types = {
            "integer",
            "bigint",
            "decimal",
            "numeric",
            "real",
            "double precision",
            "float",
            "int8",
            "int16",
            "int32",
            "int64",
            "uint8",
            "uint16",
            "uint32",
            "uint64",
            "float32",
            "float64",
        }

        time_types = {
            "timestamp",
            "date",
            "time",
            "datetime",
            "timestamp without time zone",
            "timestamp with time zone",
        }

        db_type = db_type.lower()
        if any(t in db_type for t in numeric_types):
            return "number"
        elif any(t in db_type for t in time_types):
            return "time"
        elif "bool" in db_type:
            return "boolean"
        else:
            return "string"

    def generate_schema_dict(self, table: str, columns: List[Dict]) -> Dict:
        """Generate the schema dictionary for YAML"""
        try:
            # Convert table name to PascalCase for cube name
            cube_name = "".join(word.capitalize() for word in table.split("_"))

            # Create dimensions
            dimensions = {}
            for col in columns:
                dimension_type = self.map_type(col["type"])
                dimension = {
                    "sql": f"{{CUBE}}.{col['name']}",
                    "type": dimension_type,
                    "title": " ".join(word.capitalize() for word in col["name"].split("_")),
                }

                if col["primary_key"]:
                    dimension["primaryKey"] = True

                dimensions[col["name"]] = dimension

            # Create measures
            measures = {"count": {"type": "count"}}

            # Add measures for numeric columns
            numeric_columns = [col for col in columns if self.map_type(col["type"]) == "number"]
            for col in numeric_columns:
                measures[f'{col["name"]}_sum'] = {
                    "sql": f"{{CUBE}}.{col['name']}",
                    "type": "sum",
                    "title": f"Total {' '.join(word.capitalize() for word in col['name'].split('_'))}",
                }
                measures[f'{col["name"]}_avg'] = {
                    "sql": f"{{CUBE}}.{col['name']}",
                    "type": "avg",
                    "title": f"Average {' '.join(word.capitalize() for word in col['name'].split('_'))}",
                }

            # Create the complete schema
            schema = {
                "cubes": [
                    {
                        "name": cube_name,
                        "sql": f"SELECT * FROM {table}",
                        "dataSource": self.data_store.database_type,
                        "dimensions": dimensions,
                        "measures": measures,
                        "joins": {},
                        "preAggregations": {},
                    }
                ]
            }

            return schema

        except Exception as e:
            logger.error(f"Error generating schema for table {table}", exc_info=True)
            raise

    def generate_schema_files(self) -> Dict[str, str]:
        """Generate Cube.js schema files for all tables"""
        try:
            tables = self.get_tables()
            generated_files = {}

            for table in tables:
                try:
                    logger.info(f"Processing table: {table}")

                    # Get column information
                    columns = self.get_columns(table)

                    # Generate schema
                    schema = self.generate_schema_dict(table, columns)

                    # Convert to YAML
                    yaml_content = yaml.dump(schema, sort_keys=False, indent=2, allow_unicode=True)

                    # Add to generated files
                    generated_files[f"{table}.yaml"] = yaml_content

                    logger.info(f"Generated schema for table: {table}")

                except Exception as e:
                    logger.error(f"Error generating schema for table {table}", exc_info=True)
                    raise

            return generated_files

        except Exception as e:
            logger.error("Error generating schema files", exc_info=True)
            raise


def get_schema_generator(data_store: ClientDataStore) -> SchemaGenerator:
    """Get schema generator for data store"""
    return SchemaGenerator(data_store)
