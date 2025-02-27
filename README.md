# SHACL-Shape-Generator
Python tool to automatically generate SHACL rules from ontologies in .ttl format.

Shape generation is limited to verifying the domain and range of object properties and datatype properties.  
For object properties, this corresponds to ensuring the correct start and end class.  
For datatype properties, it corresponds to verifying that the property is assigned to an instance of the correct class and that its value conforms to the specified data type.
* [Script to generate rules for datatype properties](attributes.py)
* [Script to generate rules for object properties](relationships.py)

