from stix2 import TAXIICollectionSource, Filter
from taxii2client import Collection
# Initialize dictionary to hold Enterprise ATT&CK content
attack = {}
# Establish TAXII2 Collection instance for Enterprise ATT&CK
collection = Collection("https://cti-taxii.mitre.org/stix/collections/95ecc380-afe9-11e4-9b6c-751b66dd541e/")


class MitreApi:
    def get_tactics_by_technique_id(self,technique_ids):

        # Supply the collection to TAXIICollection
        tc_source = TAXIICollectionSource(collection)
        # Create filters to retrieve content from Enterprise ATT&CK
        filter_objs = {
            "techniques": [
            Filter('type', '=', "attack-pattern"),
            Filter('external_references.external_id', 'in', technique_ids)]
        }
        for key in filter_objs:
            attack[key] = tc_source.query(filter_objs[key])
        # For visual purposes, print the first technique received
        tactics=[]
        response_data={}
        description=""
        response_data['tactics']={}
        if len( attack["techniques"])>0:
            for technique in attack["techniques"]:
                for tactic in technique["kill_chain_phases"]:
                    tactics.append(tactic['phase_name'])
                description=description+"\n"+technique['description']
        response_data['tactics']=tactics
        response_data['description']=description
        return response_data

