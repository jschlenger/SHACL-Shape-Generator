from array import typecodes
import rdflib
from rdflib.namespace import RDF, RDFS, OWL

# function to deal separately with hash and slash namespaces
# example hash namespace: http://www.w3.org/2004/02/skos/core#Concept
# example slash namespace: http://xmlns.com/foaf/0.1/Person
def getName(iri):
    if "#" in iri:
        return iri.partition('#')[2]
    elif "/" in iri:
        lastSlash = iri.rfind("/")
        return iri[lastSlash+1:]
    else:
        return iri
    
def getUnion(soi):
    returnList = set()
    unionEnd = False
    subject = soi
    for union in graph.objects(subject, OWL.unionOf):
        subject = union
        while not unionEnd:
            for first in graph.objects(subject, RDF.first):
                returnList.add(first)
            for rest in graph.objects(subject, RDF.rest):
                if rest[0:4] == "http":
                    unionEnd = True
                else:
                    subject = rest
    return returnList

def getDomains(attribute):
    returnList = set()
    for domain in graph.objects(attribute, RDFS.domain):
        if domain[0:4] == "http":
            returnList.add(domain)
        else:
            unionList = getUnion(domain)
            returnList.update(unionList)
    return returnList

# conversion table for prefixes
# this list can be adapted according to personal needs
# all prefixes defined here will also be used when writing the generated SHACL rules into the .ttl file
prefixConversion = {
    "http://www.w3.org/ns/shacl#": "sh:",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
    "http://www.w3.org/2001/XMLSchema#": "xsd:",
    "http://www.opengis.net/ont/geosparql#": "geo:",
    "https://w3id.org/bot#": "bot:",
    "http://www.w3.org/2003/01/geo/wgs84_pos#": "wgs:",
    "http://www.w3.org/2002/07/owl#": "owl:",
    "https://www.example.org#": "exa:"
}

# create new rdf graph
graph = rdflib.Graph()

# create and open .cs file 
f = open("attribute_shapes.ttl", "w+")

for prefix in prefixConversion:
    #f.write("PREFIX " + prefixConversion.get(prefix) + " <" + prefix + ">\n")
    f.write("@prefix " + prefixConversion.get(prefix) + "<" + prefix + "> .\n")
f.write("\n")

# read ontology file
format_ = rdflib.util.guess_format('ontology.ttl')
graph.parse('ontology.ttl', format=format_)

# get all attributes
attributes = set()
for s , p in graph.subject_predicates(OWL.DatatypeProperty):
    attributes.add(s)

# sort classes alphabetically (iri)
attributes = sorted(attributes)

count = 1

for attribute in attributes:

    attributeRange = ""
    for o in graph.objects(attribute, RDFS.range):
        attributeRange = o
    
    # find domains
    attributeDomains = getDomains(attribute)
    startingPoint = attribute
    while len(attributeDomains) == 0:
        for parent in graph.objects(startingPoint, RDFS.subPropertyOf):
            attributeDomains.update(getDomains(parent))
            for newParent in graph.objects(parent, RDFS.subPropertyOf):
                startingPoint = newParent
                continue
            break
        break

    # write SHACL rules into .ttl file
    if len(attributeDomains) != 0: 
        f.write("exa:attributeDomainShape_" + str(count) + " rdf:type sh:NodeShape ;\n")
        noPrefix = True
        for prefix in prefixConversion:
            if prefix in attribute: # replace ontology namespaces with prefixes
                f.write("sh:targetSubjectsOf " + attribute.replace(prefix, prefixConversion.get(prefix)) + " ;\n")
                noPrefix = False
        if noPrefix:
            f.write("sh:targetSubjectsOf " + attribute + " ;\n")
        if len(attributeDomains) == 1:
            for attributeDomain in attributeDomains:
                noPrefix = True
                for prefix in prefixConversion:
                    if prefix in attributeDomain: # replace ontology namespaces with prefixes 
                        f.write("sh:class " + attributeDomain.replace(prefix, prefixConversion.get(prefix)) + " .\n\n")
                        noPrefix = False
            if noPrefix:
                f.write("sh:class " + attributeDomain + " .\n\n")
        elif len(attributeDomains) > 1:
            f.write("sh:or (\n")
            for attributeDomain in attributeDomains:
                noPrefix = True
                for prefix in prefixConversion:
                    if prefix in attributeDomain: # replace ontology namespaces with prefixes  
                        f.write("[ sh:class " + attributeDomain.replace(prefix, prefixConversion.get(prefix)) + " ]\n")
                        noPrefix = False
            if noPrefix:
                f.write("[ sh:class " + attributeDomain + " ]\n")
            f.write(") .\n\n")
    
    if attributeRange != "":
        f.write("exa:attributeRangeShape_" + str(count) + " rdf:type sh:NodeShape ;\n")
        noPrefix = True
        for prefix in prefixConversion:
            if prefix in attribute: # replace ontology namespaces with prefixes
                f.write("sh:targetObjectsOf " + attribute.replace(prefix, prefixConversion.get(prefix)) + " ;\n")
                noPrefix = False
        if noPrefix:
            f.write("sh:targetObjectsOf " + attribute + " ;\n")
        noPrefix = True
        for prefix in prefixConversion:
            if prefix in attributeRange: # replace ontology namespaces with prefixes
                f.write("sh:datatype " + attributeRange.replace(prefix, prefixConversion.get(prefix)) + " .\n\n")
                noPrefix = False
        if noPrefix:
            f.write("sh:datatype " + attributeRange + " .\n\n")
    count = count + 1

f.close()
