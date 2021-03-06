ConnectResponse = {
    "@context": {
        "doc": "terminusdb:///system/data/",
        "layer": "http://terminusdb.com/schema/layer#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "ref": "http://terminusdb.com/schema/ref#",
        "repo": "http://terminusdb.com/schema/repository#",
        "system": "http://terminusdb.com/schema/system#",
        "terminus": "http://terminusdb.com/schema/system#",
        "vio": "http://terminusdb.com/schema/vio#",
        "woql": "http://terminusdb.com/schema/woql#",
        "xdd": "http://terminusdb.com/schema/xdd#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
    },
    "@id": "doc:anonymous",
    "@type": "system:User",
    "rdfs:comment": {"@language": "en", "@value": "This is the anonymous account"},
    "rdfs:label": {"@language": "en", "@value": "Anonymous User"},
    "system:agent_name": {"@type": "xsd:string", "@value": "anonymous"},
    "system:role": {
        "@id": "doc:anonymous_role",
        "@type": "system:Role",
        "rdfs:comment": {
            "@language": "en",
            "@value": "Role providing public access capabilities",
        },
        "rdfs:label": {"@language": "en", "@value": "Anonymous Role"},
    },
    "system:user_key_hash": "",
}
