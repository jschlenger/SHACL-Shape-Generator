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

def getRanges(relation):
    returnList = set()
    for range in graph.objects(relation, RDFS.range):
        if range[0:4] == "http":
            returnList.add(range)
        else:
            unionList = getUnion(range)
            returnList.update(unionList)
    return returnList

def getDomains(relation):
    returnList = set()
    for domain in graph.objects(relation, RDFS.domain):
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
f = open("relation_shapes.ttl", "w+")

for prefix in prefixConversion:
    #f.write("PREFIX " + prefixConversion.get(prefix) + " <" + prefix + ">\n")
    f.write("@prefix " + prefixConversion.get(prefix) + "<" + prefix + "> .\n")
f.write("\n")

# read ontology file
format_ = rdflib.util.guess_format('ontology.ttl')
graph.parse('ontology.ttl', format=format_)

# get all relations
relationships = set()
for s , p in graph.subject_predicates(OWL.ObjectProperty):
    relationships.add(s)
    for o in graph.objects(s, OWL.deprecated):
        relationships.remove(s)

# sort classes alphabetically (iri)
relationships = sorted(relationships)

count = 1

for relation in relationships:

    # find ranges (recursivly for parents)
    relationRanges = getRanges(relation)
    startingPoint = relation
    while len(relationRanges) == 0:
        for parent in graph.objects(startingPoint, RDFS.subPropertyOf):
            relationRanges.update(getRanges(parent))
            for newParent in graph.objects(parent, RDFS.subPropertyOf):
                startingPoint = newParent
                continue
            break
        break
    
    # find domains (recursivly for parents)
    relationDomains = getDomains(relation)
    startingPoint = relation
    while len(relationDomains) == 0:
        for parent in graph.objects(startingPoint, RDFS.subPropertyOf):
            relationDomains.update(getDomains(parent))
            for newParent in graph.objects(parent, RDFS.subPropertyOf):
                startingPoint = newParent
                continue
            break
        break

    # write SHACL rules into .ttl file
    if len(relationDomains) != 0: 
        f.write("exa:relationDomainShape_" + str(count) + " rdf:type sh:NodeShape ;\n")
        noPrefix = True
        for prefix in prefixConversion:
            if prefix in relation: # replace ontology namespaces with prefixes
                f.write("sh:targetSubjectsOf " + relation.replace(prefix, prefixConversion.get(prefix)) + " ;\n")
                noPrefix = False
        if noPrefix:
            f.write("sh:targetSubjectsOf " + relation + " ;\n")
        if len(relationDomains) == 1:
            for relationDomain in relationDomains:
                noPrefix = True
                for prefix in prefixConversion:
                    if prefix in relationDomain: # replace ontology namespaces with prefixes  
                        f.write("sh:class " + relationDomain.replace(prefix, prefixConversion.get(prefix)) + " .\n\n")
                        noPrefix = False
            if noPrefix:
                f.write("sh:class " + relationDomain + " .\n\n")
        elif len(relationDomains) > 1:
            f.write("sh:or (\n")
            for relationDomain in relationDomains:
                noPrefix = True
                for prefix in prefixConversion:
                    if prefix in relationDomain: # replace ontology namespaces with prefixes  
                        f.write("[ sh:class " + relationDomain.replace(prefix, prefixConversion.get(prefix)) + " ]\n")
                        noPrefix = False
            if noPrefix:
                f.write("[ sh:class " + relationDomain + " ]\n")
            f.write(") .\n\n")
    
    if len(relationRanges) != 0:
        f.write("exa:relationRangeShape_" + str(count) + " rdf:type sh:NodeShape ;\n")
        noPrefix = True
        for prefix in prefixConversion:
            if prefix in relation: # replace ontology namespaces with prefixes
                f.write("sh:targetObjectsOf " + relation.replace(prefix, prefixConversion.get(prefix)) + " ;\n")
                noPrefix = False
        if noPrefix:
            f.write("sh:targetObjectsOf " + relation + " ;\n")
        if len(relationRanges) == 1:
            for relationRange in relationRanges:
                noPrefix = True
                for prefix in prefixConversion:
                    if prefix in relationRange: # replace ontology namespaces with prefixes
                        f.write("sh:class " + relationRange.replace(prefix, prefixConversion.get(prefix)) + " .\n\n")
                        noPrefix = False
            if noPrefix:
                f.write("sh:class " + relationRange + " .\n\n")
        elif len(relationRanges) > 1:
            f.write("sh:or (\n")
            for relationRange in relationRanges:
                noPrefix = True
                for prefix in prefixConversion:
                    if prefix in relationRange: # replace ontology namespaces with prefixes   
                        f.write("[ sh:class " + relationRange.replace(prefix, prefixConversion.get(prefix)) + " ]\n")
                        noPrefix = False
            if noPrefix:
                f.write("[ sh:class " + relationRange + " ]\n")
            f.write(") .\n\n")
            
    count = count + 1

f.close()
