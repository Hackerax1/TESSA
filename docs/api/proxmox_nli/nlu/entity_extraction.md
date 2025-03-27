# entity_extraction

**Module Path**: `proxmox_nli.nlu.entity_extraction`

## Classes

### EntityExtractor

#### __init__()

Initialize entity extraction patterns and resources

#### extract_entities(query)

Extract entities from the query using regex patterns and NLTK

#### validate_entities(entities, intent)

Validate extracted entities against the required entities for the intent

