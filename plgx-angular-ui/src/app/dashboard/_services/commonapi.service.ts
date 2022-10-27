import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpInterceptor, HttpParams,HttpErrorResponse} from '@angular/common/http';
import { Router, CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { BehaviorSubject, Observable,throwError } from 'rxjs';
import { environment } from '../../../environments/environment'
// import { userList } from './_models/user';
import { catchError,map,timeout } from 'rxjs/operators';
import swal from 'sweetalert';
import { msg } from '../../dashboard/_helpers/common.msg';
import {Errorhandler} from '../../dashboard/_helpers/Errorhandler';

@Injectable({
  providedIn: 'root'
})
export class CommonapiService {

  constructor(private http: HttpClient,private handler:Errorhandler) { }
  public Dashboard(){
      return this.http.get(environment.api_url+"/dashboard").pipe(catchError(this.handler.handleError));
  }
  public Hosts_count(){
      return this.http.get(environment.api_url+"/hosts/count").pipe(catchError(this.handler.handleError));
  }

  public alerts_graph_api(source,host_identifier,rule_id,severity,verdict,startDate,endDate,search){
    return this.http.get(environment.api_url+"/alerts/graph?source="+source+"&host_identifier="+host_identifier+"&rule_id="+rule_id+"&severity="+severity+"&verdict="+verdict+"&start_date="+startDate+"&end_date="+endDate+"&search="+search).pipe(catchError(this.handler.handleError));
  }
  public alerts_graph_api_filter_with_Host_identifier(source,host_identifier,rule_id,severity,verdict,startDate,endDate,search){
    return this.http.get(environment.api_url+"/alerts/graph?source="+source+"&host_identifier="+host_identifier+"&rule_id="+rule_id+"&severity="+severity+"&verdict="+verdict+"&start_date="+startDate+"&end_date="+endDate+"&search="+search).pipe(catchError(this.handler.handleError));
  }
  public alerts_source_count_api(){
    return this.http.get(environment.api_url+"/alerts/count_by_source").pipe(catchError(this.handler.handleError));
  }
  public alerts_source_count_api_Host_identifier(host_identifier){
    return this.http.get(environment.api_url+"/alerts/count_by_source?host_identifier="+host_identifier).pipe(catchError(this.handler.handleError));
  }
  public  alerts_source_count_api_resolved(){
    return this.http.get(environment.api_url+"/alerts/count_by_source?resolved=true").pipe(catchError(this.handler.handleError));
  }
  public Hosts_main(){
      return this.http.post(environment.api_url+"/hosts", {"alerts_count":false}).pipe(catchError(this.handler.handleError));
  }
  public hostsnames_main(){
      return this.http.post(environment.api_url+"/hosts", {'platform':'windows'}).pipe(catchError(this.handler.handleError));
  }
  public hosts_filter(status, platform){
    return this.http.post(environment.api_url+"/hosts", {'status': status, 'platform':platform}).pipe(catchError(this.handler.handleError));
  }
  public host_name_api(node_id){
      let urlop = environment.api_url+"/hosts/";
      return this.http.get(urlop + node_id).pipe(catchError(this.handler.handleError));
  }
  public additional_config_api(node_id){
      return this.http.post(environment.api_url+"/hosts/additional_config", {'node_id' : node_id}).pipe(catchError(this.handler.handleError));
  }
  public view_config_api(node_id){
    return this.http.post(environment.api_url+"/hosts/config", {'node_id' : node_id}).pipe(catchError(this.handler.handleError));
  }
  public recent_activity_count_api(id){
      return this.http.post(environment.api_url+"/hosts/recent_activity/count", {'node_id' : id}).pipe(catchError(this.handler.handleError));
  }
  public recent_activity_data_api(query_name, query_id){
      let param3 = localStorage.getItem('activity_nodekey');
      return this.http.post(environment.api_url+"/hosts/recent_activity", {'node_id' : param3, 'query_name': query_name, 'start': 0, 'limit':query_id}).pipe(catchError(this.handler.handleError));
  }
  public iocs_api(){
      return this.http.get(environment.api_url+"/iocs").pipe(catchError(this.handler.handleError));
  }
  public rules_api(){
      return this.http.post(environment.api_url+"/rules",{}).pipe(catchError(this.handler.handleError));
  }
  public get_rules_api(){
    return this.http.get(environment.api_url+"/rules").pipe(catchError(this.handler.handleError));
}
  public edit_rule_api(rules_id,object){
    let rule_url = environment.api_url+"/rules/";
    return this.http.post(rule_url + rules_id,object).pipe(catchError(this.handler.handleError));
  }
  public ruleadd_api(object){
    return this.http.post(environment.api_url+"/rules/add",object).pipe(catchError(this.handler.handleError));
  }
  public update_rule_api(rule_id){
    let urlop = environment.api_url+"/rules/";
    return this.http.get(urlop + rule_id).pipe(catchError(this.handler.handleError));
  }
  public rule_alerts_export(object){
  return this.http.post(environment.api_url+"/alerts/alert_source/export",object,{ responseType: "blob",headers: { 'Content-Type': 'application/json' }}).pipe(catchError(this.handler.handleError));
  }
  public packs_api(){
      return this.http.post(environment.api_url+"/packs",{}).pipe(catchError(this.handler.handleError));
  }
  public update_queries_in_pack_api(queries_id,object){
    let urlop = environment.api_url+"/queries/";
    return this.http.post(urlop + queries_id,object,{ headers: { 'Content-Type': 'application/json' }}).pipe(catchError(this.handler.handleError));
  }
  public queries_api(){
      return this.http.post(environment.api_url+"/queries",{}).pipe(catchError(this.handler.handleError));
  }
  public queriesadd_api(object){
      return this.http.post(environment.api_url+"/queries/add",object).pipe(catchError(this.handler.handleError));
  }
  public update_queries_in_query_api(queries_id,object){
    let urlop = environment.api_url+"/queries/";
    return this.http.post(urlop + queries_id,object,{ headers: { 'Content-Type': 'application/json' }}).pipe(catchError(this.handler.handleError));
  }
  public Alert_data(alert_id){
    let urlop = environment.api_url+"/alerts/";
    return this.http.get(urlop + alert_id).pipe(catchError(this.handler.handleError));
  }
  public addNote(data, alert_id){
    let urlop = environment.api_url+"/alerts/";
    return this.http.post(urlop + alert_id +"/analyst/notes",{'notes': data}).pipe(catchError(this.handler.handleError));
  }
  public getNotes_api(alert_id){
    let urlop = environment.api_url+"/alerts/";
    return this.http.get(urlop + alert_id +"/analyst/notes").pipe(catchError(this.handler.handleError));
  }
  public editNote_api(notes, note_id, alert_id){
    let urlop = environment.api_url+"/alerts/";
    return this.http.put(urlop + alert_id +"/analyst/notes", {"notes": notes, "note_id":note_id}).pipe(catchError(this.handler.handleError));
  }
  public deleteNote_api(note_id, alert_id){
    let urlop = environment.api_url+"/alerts/";
    const options = {
      headers: new HttpHeaders({
        'Content-Type': 'application/json',
      }),
      body: {
        "note_id":note_id
      }
    };
    return this.http.delete(urlop + alert_id +"/analyst/notes", options).pipe(catchError(this.handler.handleError));
  }
  public Alert_system_events_and_state_data(alert_id){
    let urlop = environment.api_url+"/alerts/"+alert_id+"/events";
    return this.http.get(urlop).pipe(catchError(this.handler.handleError));
  }
  public get_alerts_aggregated_data(alert_id){
    let urlop = environment.api_url+"/alerts/"+alert_id+"/alerted_events";
    return this.http.post(urlop,null).pipe(catchError(this.handler.handleError));
  }
  public get_host_state_details(alert_id){
    let urlop = environment.api_url+"/alerts/"+alert_id+"/state";
    return this.http.get(urlop).pipe(catchError(this.handler.handleError));
  }
  public Alerts(alertName, alertCount){
      return this.http.post(environment.api_url+"/alerts", {'source': alertName, 'startPage': 0, 'perPageRecords': alertCount }).pipe(catchError(this.handler.handleError));
  }
  public AlertsResolve(alerts_data){
    let urlresolve = environment.api_url+"/alerts";
    return this.http.put(urlresolve,alerts_data).pipe(catchError(this.handler.handleError));
  }
  public DisableHost(host_id){
    let urlresolve = environment.api_url+"/hosts/";
    let url_file = (urlresolve + host_id + "/delete");
    return this.http.put(url_file, {}).pipe(catchError(this.handler.handleError));
  }
  public hosts_enablenodes_api(host_id){
    let urlresolve = environment.api_url+"/hosts/";
    let url_file = (urlresolve + host_id + "/enable");
    return this.http.put(url_file, {}).pipe(catchError(this.handler.handleError));
  }
  public Alerts_data_count(){
    return this.http.post(environment.api_url+"/alerts", {'startPage': 0,'limit':10}).pipe(catchError(this.handler.handleError));
}
  public get_Query_data(query_id){
    let urlop = environment.api_url+"/queries/";
    return this.http.get(urlop + query_id).pipe(catchError(this.handler.handleError));
  }
  public Openc2_api(){

      return this.http.post(environment.api_url+"/response",{}).pipe(catchError(this.handler.handleError));
  }
  // Start Management
  public changePassword(Old_password, New_password, Confirm_new_password){
      return this.http.put(environment.api_url+"/users/me/password",
        {
          'old_password': Old_password,
          'new_password': New_password,
          'confirm_new_password': Confirm_new_password
        }
      ).pipe(catchError(this.handler.handleError));
  }

  public configuredEmail(){
      return this.http.get<any>(environment.api_url+"/email/configure").pipe(catchError(this.handler.handleError));
  }
  // public configuredEmailSubmit(email,password,server,port,recepient){
  //     return this.http.post(environment.api_url+"/email/configure",{"emailRecipients":recepient, "email":email, "smtpAddress":server, "password":password,"smtpPort":port});
  // }

  public UpdateconfigureEmail(SenderEmail, SenderPassword, SmtpAddress, SmtpPort, EmailRecipients,use_ssl,use_tls){
      return this.http.post(environment.api_url+"/email/configure",
        {
          "emailRecipients": EmailRecipients,
          "email": SenderEmail,
          "smtpAddress": SmtpAddress,
          "password": SenderPassword,
          "smtpPort": SmtpPort,
          "use_ssl":use_ssl,
          "use_tls":use_tls
        }
      ).pipe(catchError(this.handler.handleError));
  }
  public TestEmail(EmailRecipients, SenderEmail, SmtpAddress, SenderPassword, SmtpPort,use_ssl,use_tls){
    return this.http.post(environment.api_url+"/email/test",
    {
      "emailRecipients": EmailRecipients,
      "email": SenderEmail,
      "smtpAddress": SmtpAddress,
      "password": SenderPassword,
      "smtpPort": SmtpPort,
      "use_ssl":use_ssl,
      "use_tls":use_tls
    }
  ).pipe(timeout(60000),catchError(this.handler.handleError));
  }

  public updatePurgeData(NumberOfDays){
      return this.http.post(environment.api_url+"/management/purge/update",
        {
          'days': NumberOfDays
        }
      ).pipe(catchError(this.handler.handleError));
  }
  public getPurgeData(){
    return this.http.get(environment.api_url+"/management/purge/update").pipe(catchError(this.handler.handleError));
  }
  public getConfigurationSettings(){
    return this.http.get<any>(environment.api_url+"/management/settings").pipe(catchError(this.handler.handleError));
}
public putConfigurationSettings(settings){
  return this.http.put(environment.api_url+"/management/settings",settings).pipe(catchError(this.handler.handleError));
}
public getAntiVirusEngines(){
  return this.http.get(environment.api_url+"/management/virustotal/av_engine").pipe(catchError(this.handler.handleError));
}
public postAntiVirusEngines(data){
  return this.http.post(environment.api_url+"/management/virustotal/av_engine",data).pipe(catchError(this.handler.handleError));
}

  // END Management

  public carves_api(){
    return this.http.post(environment.api_url+"/carves", {}).pipe(catchError(this.handler.handleError));
}
public carves_download_api(carves_id){

  let urlop = environment.api_url+"/carves/download/";
  return this.http.get(urlop + carves_id,{responseType: "blob",reportProgress:true,observe:"events"}).pipe(catchError(this.handler.handleError));
  //return this.http.get(urlop + carves_id,{responseType: "blob", headers: {'Accept': 'application/tar'}});
  }
public carves_delete_api(session_id){
  return this.http.post(environment.api_url+"/carves/delete", {"session_id": session_id}).pipe(catchError(this.handler.handleError));
}

public yara_add_api(file_data: File, platform_val){
      var uploadData = new FormData();
      uploadData.append('file', file_data[0], file_data[0].name);
      uploadData.append('platform', platform_val);
      console.log(uploadData);
    return this.http.post(environment.api_url+"/yara/add", uploadData).pipe(catchError(this.handler.handleError));
}
public yara_view_api(event_type,platform_val){
    return this.http.post(environment.api_url+"/yara/view", {"file_name": event_type, "platform":platform_val}).pipe(catchError(this.handler.handleError));
}
public yara_edit_api(file_name,platform_val){
    return this.http.put(environment.api_url+"/yara/update", {"file_name": file_name, "platform":platform_val}).pipe(catchError(this.handler.handleError));
}
public yara_delete_api(yara_name,platform_val){
    return this.http.post(environment.api_url+"/yara/delete", {"file_name": yara_name, "platform":platform_val}).pipe(catchError(this.handler.handleError));
}
public yara_api(){
    return this.http.get(environment.api_url+"/yara").pipe(catchError(this.handler.handleError));
}

public ioc_api(){
    return this.http.get(environment.api_url+"/iocs").pipe(catchError(this.handler.handleError));
}
public ioc_update_api(object){
  console.log("IOC_services",environment.api_url+"/iocs/add",object);
return this.http.post(environment.api_url+"/iocs/add",object).pipe(catchError(this.handler.handleError));
}
public status_log(res_id){
  return this.http.post(environment.api_url+"/hosts/status_logs", {"node_id" : res_id}).pipe(catchError(this.handler.handleError));
}
public hosts_export(){
  return this.http.get(environment.api_url+"/hosts/export",{ headers: { 'Content-Type': 'text/csv;charset=utf-8;' }}).pipe(catchError(this.handler.handleError));
}

public response_action(res_id){
    return this.http.post(environment.api_url+"/response/status", {"node_id" : res_id})
}
public Distrbuted_row(res_id){
    return this.http.post(environment.api_url+"/distributed/add", {"node_id" : res_id}).pipe(catchError(this.handler.handleError));
}

public Hosts_data(){
    return this.http.post(environment.api_url+"/hosts", {"status":true, "alerts_count":false}).pipe(catchError(this.handler.handleError));
}
public Apikey_data(){
    return this.http.get(environment.api_url+"/management/apikeys").pipe(catchError(this.handler.handleError));
}
public Apikey_postdata(ibmxForceKey,ibmxForcePass,vt_key,alienVaultOTXKey){
    return this.http.post(environment.api_url+"/management/apikeys",{"IBMxForceKey":ibmxForceKey,"IBMxForcePass":ibmxForcePass,"vt_key":vt_key,"otx_key":alienVaultOTXKey}).pipe(catchError(this.handler.handleError));
}
public Response_action_add(action, actuator_id,tags,osName, target, file_name, file_hash){
    return this.http.post(environment.api_url+"/response/add",{
      "action": action,
      "actuator_id": actuator_id,
      "tags":tags,
      "os_name":osName,
      "target": target,
      "file_name": file_name,
      "file_hash": file_hash
    }).pipe(catchError(this.handler.handleError));
}
public Response_process_action_add(action, actuator_id,tags,osName, target, process_name, pid){
  console.log(action, actuator_id,tags,osName, target, process_name, pid)
  return this.http.post(environment.api_url+"/response/add",{
    "action": action,
    "actuator_id": actuator_id,
    "tags":tags,
    "os_name":osName,
    "target": target,
    "process_name": process_name,
    "pid": pid
  }).pipe(catchError(this.handler.handleError));
}

public Response_network_add(object){
  console.log(object);
      return this.http.post(environment.api_url+"/response/add",object).pipe(catchError(this.handler.handleError));
}
public Response_script_add(host_identifier,tags,osName, file_type, isVisible,params, file_data: File, script_name){
  var uploadData = new FormData();
  uploadData.append('host_identifier', host_identifier);
  uploadData.append('tags', tags);
  uploadData.append('os_name', osName);
  uploadData.append('file_type', file_type);
  uploadData.append('save_script', isVisible);
  uploadData.append('params', params);
  uploadData.append('file', file_data[0], file_data[0].name);
  uploadData.append('script_name', script_name);
  return this.http.post(environment.api_url+"/response/custom-action",uploadData).pipe(catchError(this.handler.handleError));
}

public Response_script_add_content(host_identifier,tags,osName, file_type, isVisible,params, content, script_name){
  return this.http.post(environment.api_url+"/response/custom-action",{
    "host_identifier": host_identifier,
    "tags":tags,
    "os_name":osName,
    "file_type": file_type,
    "save_script": isVisible,
    "params": params,
    "content": content,
    "script_name":script_name
  }).pipe(catchError(this.handler.handleError));
}

public Response_agent_update(user_name, password,type, target, actuator_id,){
  console.log(user_name,password,type, actuator_id, target)
  return this.http.post(environment.api_url+"/response/add",{
    "action": "upgrade",
    "actuator_id": actuator_id,
    "host_user":user_name,
    "host_password": password,
    "type":type,
    "target": target
  }).pipe(catchError(this.handler.handleError));
}

public Response_agent_uninstall(user_name, password,type, actuator_id){
  console.log(user_name,password,type, actuator_id)
  return this.http.post(environment.api_url+"/response/agent_uninstall",{
    "host_identifier": actuator_id,
    "user":user_name,
    "password": password,
    "type":type,
  }).pipe(catchError(this.handler.handleError));
}

  public update_queries_api(queries_id){
      let urlop = environment.api_url+"/queries/";
      return this.http.get(urlop + queries_id).pipe(catchError(this.handler.handleError));
  }

  public configs_api(){
    return this.http.get(environment.api_url+"/configs").pipe(catchError(this.handler.handleError));
  }
  public configs_Make_it_default_api(id){
    return this.http.put(environment.api_url+"/configs/"+id+"/default",{}).pipe(catchError(this.handler.handleError));
  }


  public config_upload(id,object){
    return this.http.put(environment.api_url+"/configs/"+id, object).pipe(catchError(this.handler.handleError));
    }

  public add_custom_config(object){
  return this.http.post(environment.api_url+"/configs", object).pipe(catchError(this.handler.handleError));
  }
  public delete_config(id){
    return this.http.delete(environment.api_url+"/configs/"+id).pipe(catchError(this.handler.handleError));
  }
  public asign_config_to_hosts(id,list_of_host_identifiers){
    return this.http.put(environment.api_url+"/configs/"+id+"/assign",list_of_host_identifiers).pipe(catchError(this.handler.handleError));
  }
  public get_list_of_hosts(platform){
    return this.http.post(environment.api_url+"/hosts", {'platform':platform}).pipe(catchError(this.handler.handleError));
  }
  public options_api(){
    return this.http.get(environment.api_url+"/options").pipe(catchError(this.handler.handleError));
}
public options_upload(object){
return this.http.post(environment.api_url+"/options/add",object).pipe(catchError(this.handler.handleError));
}


public associated_api(body){
return this.http.post(environment.api_url+"/queries/packed", body).pipe(catchError(this.handler.handleError));
}
  public pack_upload_api(file_data: File, category_val){
    console.log(file_data);
    var pack_uploadData = new FormData();
    pack_uploadData.append('category',category_val);
    pack_uploadData.append('file', file_data[0], file_data[0].name);

    return this.http.post(environment.api_url+"/packs/upload", pack_uploadData).pipe(catchError(this.handler.handleError));
  }

  public Queries_add_api(object){
    console.log("Payload is ",object);
    return this.http.post(environment.api_url+"/distributed/add", object).pipe(catchError(this.handler.handleError));
  }

  public live_Queries_tables_schema(){
    return this.http.get(environment.api_url+"/schema?export_type=json").pipe(catchError(this.handler.handleError));
}
  //Begin:: Tags
   public Tags_data(){
     return this.http.get(environment.api_url+"/tags").pipe(catchError(this.handler.handleError));
   }
   public tags_api(){
     return this.http.get(environment.api_url+"/tags").pipe(catchError(this.handler.handleError));
   }
   public add_tags_api(tags_val){
     console.log(tags_val);
      return this.http.post(environment.api_url+"/tags/add", {'tag':tags_val}).pipe(catchError(this.handler.handleError));
   }
   public delete_tags_api(tags_val){
     return this.http.post(environment.api_url+"/tags/delete",{"tag":tags_val}).pipe(catchError(this.handler.handleError));
   }
   //Host
   public hosts_addtag_api(node_id,tags){
     let urlop = environment.api_url+"/hosts/";
     let tags_list = tags.split(',');
     return this.http.post(urlop + node_id + '/tags', {'tag':tags_list[tags_list.length-1]}).pipe(catchError(this.handler.handleError));
   }
   public hosts_removetags_api(node_id,tag){
     let urlop = environment.api_url+"/hosts/";
     const options = {
       headers: new HttpHeaders({
         'Content-Type': 'application/json',
       }),
       body: {
         "tag":tag
       }
     };
     // console.log(urlop + node_id + '/tags', options);
     return this.http.delete(urlop + node_id + '/tags', options).pipe(catchError(this.handler.handleError));
   }
   //Packs
   public packs_addtag_api(pack_id,tags){
     let urlop = environment.api_url+"/packs/";
     let tags_list = tags.split(',');
     return this.http.post(urlop + pack_id + '/tags', {'tag':tags_list[tags_list.length-1]}).pipe(catchError(this.handler.handleError));
   }
   public packs_removetags_api(pack_id,tag){
     let urlop = environment.api_url+"/packs/";
     const options = {
       headers: new HttpHeaders({
         'Content-Type': 'application/json',
       }),
       body: {
         "tag":tag
       }
     };
     return this.http.delete(urlop + pack_id + '/tags', options).pipe(catchError(this.handler.handleError));
   }
   //Queries
   public queries_addtag_api(query_id,tags){
     let urlop = environment.api_url+"/queries/";
     let tags_list = tags.split(',');
     return this.http.post(urlop + query_id + '/tags', {'tag':tags_list[tags_list.length-1]});
   }
   public queries_removetags_api(query_id,tag){
     let urlop = environment.api_url+"/queries/";
     const options = {
       headers: new HttpHeaders({
         'Content-Type': 'application/json',
       }),
       body: {
         "tag":tag
       }
     };
     return this.http.delete(urlop + query_id + '/tags', options).pipe(catchError(this.handler.handleError));
   }
   //Tagged
   public tagged_api(tags_val){
     return this.http.post(environment.api_url+"/tags/tagged", {"tags":tags_val}).pipe(catchError(this.handler.handleError));
   }
   public host_tagged_api(hosttags_val){
     return this.http.post(environment.api_url+"/hosts/tagged", {"tags":hosttags_val}).pipe(catchError(this.handler.handleError));
   }
   public pack_tagged_api(packtags_val){
     return this.http.post(environment.api_url+"/packs/tagged", {"tags":packtags_val}).pipe(catchError(this.handler.handleError));
   }
   public query_tagged_api(qrytags_val){
     return this.http.post(environment.api_url+"/queries/tagged", {"tags":qrytags_val}).pipe(catchError(this.handler.handleError));
   }
   //End:: Tags

   public search_csv_export(object){

    return this.http.post(environment.api_url+"/hosts/search/export",object,{responseType: "blob", headers: {'Accept': 'application/csv'}}).pipe(catchError(this.handler.handleError));
    }

    public alerts_export(object){
      return this.http.post(environment.api_url+"/alerts/alert_source/export",object,{responseType: "blob", headers: {'Accept': 'application/csv'}}).pipe(catchError(this.handler.handleError));
    }

    public recent_activity_search_csv_export(object){

    return this.http.post(environment.api_url+"/hosts/search/export",object,{responseType: "blob", headers: {'Accept': 'application/csv'}}).pipe(catchError(this.handler.handleError));
    }

    public Alerted_entry(alert_id){
      let urlop = environment.api_url+"/alerts/";
      return this.http.get(urlop + alert_id).pipe(catchError(this.handler.handleError));
    }
    public cpt_restart_api(host_identifier){
      return this.http.post(environment.api_url+"/response/restart-agent", {"host_identifier":host_identifier}).pipe(catchError(this.handler.handleError));
    }
    public cpt_upgrade_api(host_identifier){
      return this.http.post(environment.api_url+"/response/agent_uninstall", {"host_identifier":host_identifier}).pipe(catchError(this.handler.handleError));
    }

    public delete_host(host_id){
      let urlop = environment.api_url+"/hosts/";
     const options = {
       headers: new HttpHeaders({
         'Content-Type': 'application/json',
       })
     };
     // console.log(urlop + node_id + '/tags', options);
     return this.http.delete(urlop + host_id + '/delete', options).pipe(catchError(this.handler.handleError));

    }
    public deleteApipacks(pack_id){
      let urlop = environment.api_url+"/packs/";
     const options = {
       headers: new HttpHeaders({
         'Content-Type': 'application/json',
       })
     };
     // console.log(urlop + node_id + '/tags', options);
     return this.http.delete(urlop + pack_id + '/delete', options).pipe(catchError(this.handler.handleError));
    }
    public deleteApiQueries(query_id){
      let urlop = environment.api_url+"/queries/";
     const options = {
       headers: new HttpHeaders({
         'Content-Type': 'application/json',
       })
     };
     // console.log(urlop + node_id + '/tags', options);
     return this.http.delete(urlop + query_id + '/delete', options).pipe(catchError(this.handler.handleError));

    }
    public deleteApiresponse(response_id){
      let urlop = environment.api_url+"/response/";
     const options = {
       headers: new HttpHeaders({
         'Content-Type': 'application/json',
       })
     };
     // console.log(urlop + node_id + '/tags', options);
     return this.http.delete(urlop + response_id + '/delete', options).pipe(catchError(this.handler.handleError));
    }

    public Host_rules_api(id){
      const options = {
        headers: new HttpHeaders({
        })
      };
        return this.http.get(environment.api_url+"/hosts/"+id+"/alerts/distribution",options).pipe(catchError(this.handler.handleError));
    }

    public Scan_now(object){
      const options = {
        headers: new HttpHeaders({
          'Content-Type': 'application/json',
        })
      };
        return this.http.post(environment.api_url+"/defender-management/scan-now",object).pipe(catchError(this.handler.handleError));
    }

    public Schedule_scan(object){
        return this.http.post(environment.api_url+"/defender-management/schedule-scan",object).pipe(catchError(this.handler.handleError));
    }

    public Exclusions(object){
        return this.http.post(environment.api_url+"/defender-management/configure",object).pipe(catchError(this.handler.handleError));
    }

    public Current_Setting(object){
        return this.http.post(environment.api_url+"/defender-management/current-settings",object).pipe(catchError(this.handler.handleError));
    }

    public viewopenc2(object){
        return this.http.post(environment.api_url+"/response/view",object).pipe(catchError(this.handler.handleError));
    }

    public Checkupdate(object){
        return this.http.post(environment.api_url+"/defender-management/check-update",object).pipe(catchError(this.handler.handleError));
    }
    public Getquarantine(object){
        return this.http.post(environment.api_url+"/defender-management/get-quarantine",object).pipe(catchError(this.handler.handleError));
    }

    public Computerstatus(object){
        return this.http.post(environment.api_url+"/defender-management/computer-status",object).pipe(catchError(this.handler.handleError));
    }
    public defenderStatus_refresh(object){
      return this.http.post(environment.api_url+"/defender-management/status_refresh",object).pipe(catchError(this.handler.handleError));
    }
    public live_Terminal_response(object){
      return this.http.post(environment.api_url+"/response/live_response",object).pipe(catchError(this.handler.handleError));
    }
  public get_server_metrics(object){
    return this.http.post(environment.api_url+"/management/metrics",object).pipe(catchError(this.handler.handleError));
  }
    public hoststatuslogexport(object){
       // return this.http.post(environment.api_url+"/defender-management/event_logs",object,{ responseType: "blob",headers: { 'Content-Type': 'application/json' }}).pipe(catchError(this.handler.handleError));
       return this.http.post(environment.api_url+"/hosts/status_log/export",object).pipe(catchError(this.handler.handleError));
    }
    public Verifypassword(object){
      return this.http.post(environment.api_url+"/management/verifypw",object).pipe(catchError(this.handler.handleError));
    }
    public carve_Quarantine_Threat(object){
      return this.http.post(environment.api_url+"/defender-management/quarantine_file/carve",object).pipe(catchError(this.handler.handleError));
    }
    public Cancel_viewresponse(object){
     return this.http.post(environment.api_url+"/response/cancel",object).pipe(catchError(this.handler.handleError));
   }
   public customActionContentScript(fileName){
    return this.http.get('assets/script/'+fileName, { responseType: 'text'}).pipe(catchError(this.handler.handleError));
  }
  public alertedEventsExport(id,queryName){
    return this.http.get(environment.api_url+"/alerts/"+id+"/alerted_events/export?query_name="+queryName,{responseType: "blob", headers: {'Accept': 'application/csv'}}).pipe(catchError(this.handler.handleError));
  }
  public responseStatus(){
    return this.http.get(environment.api_url+"/response/status/all");
  }
  public tagsBulkAssignApi(body,tagName){
    return this.http.put(environment.api_url+"/tags/"+tagName ,body).pipe(catchError(this.handler.handleError));
  }


  // Start :: RBAC
  public getUsersDetails(){
    return this.http.get(environment.api_url+"/users").pipe(catchError(this.handler.handleError));
  }
  public getUser(id){
    return this.http.get(environment.api_url+"/users/user/"+id).pipe(catchError(this.handler.handleError));
  }
  public editUserForm(userName,payload){
    return this.http.put(environment.api_url+"/users/user/"+userName,payload).pipe(catchError(this.handler.handleError));
  }
  public createUser(object){
    return this.http.post(environment.api_url+"/users",object).pipe(catchError(this.handler.handleError));
  }
  public changeUserPassword(userName,object){
    return this.http.put(environment.api_url+"/users/user/"+userName+"/password",object).pipe(catchError(this.handler.handleError));
  }
  public changeUserDetails(object){
    return this.http.put(environment.api_url+"/users/me",object).pipe(catchError(this.handler.handleError));
  }
  public getUserDetails(){
    return this.http.get(environment.api_url+"/users/me",{}).pipe(catchError(this.handler.handleError));
  }
  // End :: RBAC

  public getSSOLoginURL(){
    return environment.api_url+"/sso/login";
  }
  public logout(){
    return this.http.post(environment.api_url+"/logout",{}).pipe(catchError(this.handler.handleError));
  }

  public getSSOStatus(){
    return this.http.get(environment.api_url+"/index",{}).pipe(catchError(this.handler.handleError));
  }

  public getLogServer(serverName){
    return this.http.get(environment.api_url+"/management/log_setting?server_name="+serverName).pipe(catchError(this.handler.handleError));
  }
  public updateLogSetting(object){
    console.log(object);
    return this.http.put(environment.api_url+"/management/log_setting",object).pipe(catchError(this.handler.handleError));
  }
  public manualPurge(object){
    return this.http.post(environment.api_url+"/management/manual_purge",object).pipe(catchError(this.handler.handleError));
  }
  public getLogFile(serverName){
    return this.http.get(environment.api_url+"/management/download_log?server_name="+serverName).pipe(catchError(this.handler.handleError));
  }
  public downloadLog(object){
    return this.http.post(environment.api_url+"/management/download_log",object,{responseType: "blob", headers: {'Accept': 'application/csv'}}).pipe(catchError(this.handler.handleError));
  }
  public bulkDisableHost(object){
    return this.http.put(environment.api_url+"/hosts/delete", object).pipe(catchError(this.handler.handleError));
  }
  public bulkRestoreHost(object){
    return this.http.post(environment.api_url+"/hosts/enable", object).pipe(catchError(this.handler.handleError));
  }
  public bulkDeleteHost(object){
    const payload = {
      headers: new HttpHeaders({
        'Content-Type': 'application/json',
      }),
      body: object
    };
    return this.http.delete(environment.api_url+"/hosts/delete", payload).pipe(catchError(this.handler.handleError));
  }
  public bulkDeleteResponse(object){
    const payload = {
      headers: new HttpHeaders({
        'Content-Type': 'application/json',
      }),
      body: object
    };
    return this.http.delete(environment.api_url+"/response/delete", payload).pipe(catchError(this.handler.handleError));
  }
  public bulkDisableRules(object){
    return this.http.post(environment.api_url+"/rules/disable", object).pipe(catchError(this.handler.handleError));
  }
  public enableRules(object){
    return this.http.post(environment.api_url+"/rules/enable", object).pipe(catchError(this.handler.handleError));
  }
  public bulkDeleteRules(object){
    const payload = {
      headers: new HttpHeaders({
        'Content-Type': 'application/json',
      }),
      body: object
    };
    return this.http.delete(environment.api_url+"/rules/disable", payload).pipe(catchError(this.handler.handleError));
  }
}
