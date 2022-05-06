from polylogyx.models import db, Rule

def get_rule_by_id(rule_id):
    return Rule.query.filter(Rule.id == rule_id).first()

def get_rule_name_by_id(rule_id):
    rule=Rule.query.filter(Rule.id == rule_id).first()
    return rule.name

def get_all_rules():
    return Rule.query.all()

def get_rule_by_name(rule_name):
    return Rule.query.filter(Rule.name == rule_name).first()

def edit_rule_by_id(rule_id,name,alerters,description,conditions,status,updated_at,recon_queries,severity,type_ip,tactics,technique_id):
    rule = get_rule_by_id(rule_id)
    return rule.update(name=name,alerters=alerters,description=description,conditions=conditions,status=status,updated_at=updated_at,recon_queries=recon_queries,severity=severity,type_ip=type_ip,tactics=tactics,technique_id=technique_id)

def create_rule_object(name,alerters,description,conditions,status,type_ip,tactics,technique_id,updated_at,recon_queries,severity):
    return Rule(name=name,alerters=alerters,description=description,conditions=conditions,status=status,type=type_ip,tactics=tactics,technique_id=technique_id,recon_queries=recon_queries,severity=severity)
