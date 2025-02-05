from enum import Enum
from mongoengine import fields


class SemanticEngineType(str, Enum):
    CUBEJS = "cubejs"


class SemanticLayerConfig(fields.EmbeddedDocument):
    """Generic configuration for semantic layer engines"""

    api_url = fields.StringField(required=True)
    api_token = fields.StringField(required=True)
    dev_mode = fields.BooleanField(default=False)
    additional_config = fields.DictField(default={})


class RepositoryConfig(fields.EmbeddedDocument):
    """Configuration for GitHub repository access"""

    repo_url = fields.StringField(required=True)
    branch = fields.StringField(required=True, default="main")
    api_key = fields.StringField(required=True)
    base_path = fields.StringField(default="")
