import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../../dashboard/_services/commonvariable.service';
import { FormGroup, FormBuilder, FormArray, Validators } from '@angular/forms';
// import { QueryBuilderConfig, QueryBuilderComponent, QueryBuilderClassNames } from 'angular2-query-builder';
import swal from 'sweetalert';
import { first } from 'rxjs/operators';
import { json } from 'd3';
import { Location } from '@angular/common';
// import Swal from 'sweetalert2'
import { HttpClient, HttpResponse } from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import { Title } from '@angular/platform-browser';
import { AuthorizationService } from '../../../dashboard/_services/Authorization.service';


declare  function init_querybuilder([]): any;
export class Expertise {
  id: number;
  itenName: string;
}
class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}
@Component({
  selector: 'app-edit-rule',
  templateUrl: './edit-rule.component.html',
  styleUrls: ['./edit-rule.component.css']
})
export class EditRuleComponent implements OnInit {
  id:any;
  sub:any;
ruledata: any = [];
ruledata_data: any = []
updateRule: FormGroup;
name:any;
sample_data:any =[];
loading = false;
submitted = false;
public RuleObj: any = {
  alerters:[],
  tactics:[]
}
updateRuleObj: any;
rule_name:string;
query_rules:any=[];
query_condition:any =[];
query:any;
query_builder:any;
result:any;
error:any;
Updated:any;
// config:any;
mitre_show:boolean = false;
type_selected:boolean;
public selected_alerts: any = [];
dropdownAlertList = [];
selectedAlertItems = [];
dropdownAlertSettings = {};
public rule_alert :any = [];

dropdownTacticsList = [];
selectedTacticsItems = [];
dropdownTacticsSettings = {};
public rule_tactics :any = [];

public tactics_list:any;
tactics_data:any[]
tactics_tech_data :any = [];

radioItems: Array<string>;
model = { rule_type: 'MITRE' };
isEmailEnabled = false;
isAddDescriptionEmail = false;
hasAcess=this.authorizationService.hasAccess()
  constructor(
    private _Activatedroute: ActivatedRoute,
    private commonapi: CommonapiService,
    private commonvariable: CommonVariableService,
    private fb: FormBuilder,
    private _location: Location,
    private http: HttpClient,
    private router: Router,
    private titleService: Title,
    private authorizationService: AuthorizationService,

  ) {this.radioItems = ['DEFAULT', 'MITRE'];
  this.updateRule= this.fb.group({
    name:['', Validators.required],
    description:'',
    alerters:'',
    conditions:'',
    status:'',
    severity:'',
    rule_type:'',
    technique_id:'',
    tactics:'',
    platform:''
  }) }

  ngOnInit() {
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Rule");

    this.dropdownAlertSettings = {
      singleSelection: false,
      text: "Nothing selected",
      selectAllText:'Select All',
      unSelectAllText:'UnSelect All',
      badgeShowLimit:2,
      enableSearchFilter:true,
      classes: "angular-multiselect-class",
      searchPlaceholderText: "Search alerts here.."
    };

    this.dropdownAlertList = [
      {"id":1,"itemName":"Rsyslog","value":"rsyslog"},
      {"id":2,"itemName":"Email","value":"email"}
    ];

    this.dropdownTacticsSettings = {
      singleSelection: false,
      text: "Nothing selected",
      selectAllText:'Select All',
      unSelectAllText:'UnSelect All',
      badgeShowLimit:1,
      enableSearchFilter:true,
      classes: "angular-multiselect-class",
      searchPlaceholderText: "Search Tactics here.."
    };

    this.dropdownTacticsList = [
      {"id":"initial-access","itemName":"Initial Access"},
      {"id":"execution","itemName":"Execution"},
      {"id":"persistence","itemName":"Persistence"},
      {"id":"privilege-escalation","itemName":"Privilege Escalation"},
      {"id":"defense-evasion","itemName":"Defense Evasion"},
      {"id":"credential-access","itemName":"Credential Access"},
      {"id":"discovery","itemName":"Discovery"},
      {"id":"lateral-movement","itemName":"Lateral Movement"},
      {"id":"collection","itemName":"Collection"},
      {"id":"command-and-control","itemName":"Command and Control"},
      {"id":"exfiltration","itemName":"Exfiltration"},
      {"id":"impact","itemName":"Impact"}
    ];


    this.sub = this._Activatedroute.paramMap.subscribe(params => {
      this.id = params.get('id');
       if(isNaN(this.id)){
	      this.pagenotfound();
       }
      let additional_config =this.commonapi.update_rule_api(this.id).subscribe(res =>{
        this.ruledata=res;
        if(this.ruledata.status == "failure"){
          this.pagenotfound();
        }
        else{
        this.ruledata_data=this.ruledata.data;
        this.rule_name=this.ruledata_data.name
        this.query_rules=this.ruledata_data.conditions;
        this.query_condition=this.ruledata_data.conditions.condition;
        init_querybuilder(this.query_rules);
        /* Mitre and default radio button edit start*/
        if(this.ruledata_data.type==null){
          this.ruledata_data['type']="DEFAULT"
        }
        this.model.rule_type = this.ruledata_data.type;
          if(this.model.rule_type == 'MITRE'){
          this.mitre_show = true;
        } else{
          this.mitre_show = false;
        }
        /* Mitre and default radio button edit End*/
        // if(this.ruledata_data.alert_description == true){ this.isEmailEnabled  = true}
        this.selectedAlertItems = this.getAlertersDict(this.ruledata_data.alerters);
        this.selectedTacticsItems = this.getTacticsDict(this.ruledata_data.tactics);
        this.enableAddDescriptionEmail(true);
      }
      })
    });
  }
  get f() { return this.updateRule.controls; }

  onSubmit() {
    this.submitted = true;
    if (this.updateRule.invalid) {
      return;
    }

    $(document).ready(() => {
      this.query_builder = $('#rules-hidden').val();
      if(this.query_builder == '')
        return;
      else{
        let selected_alerts = this.f.alerters.value;
      let selected_tactics = this.f.tactics.value;
      this.updateRuleObj={
        "name":this.f.name.value,
        "description":this.f.description.value,
        "alerters":this.f.alerters.value,
        "status":this.f.status.value,
        "severity":this.f.severity.value,
        "platform":this.f.platform.value,
        "alert_description":this.isAddDescriptionEmail,
        "type":this.f.rule_type.value,
      }
      var alerters_array = [];
      var tactics_array = [];

      for(const index in selected_alerts){
          alerters_array.push(selected_alerts[index]['value']);
      }

      for(const index in selected_tactics){
          tactics_array.push(selected_tactics[index]['id']);
      }


      if(this.f.rule_type.value == 'MITRE'){
        this.updateRuleObj["technique_id"] = this.f.technique_id.value;
        this.updateRuleObj["tactics"] = this.getStringConcatinated(tactics_array);
      }else{
        this.updateRuleObj["technique_id"] = '';
        this.updateRuleObj["tactics"] = '';
      }
      this.updateRuleObj["alerters"] = this.getStringConcatinated(alerters_array);

      this.updateRuleObj["conditions"]= JSON.parse(this.query_builder);
      this.http.post<DataTablesResponse>(environment.api_url+"/rules/"+this.id, this.updateRuleObj,{ headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res =>{

        this.result=res;
        if(this.result && this.result.status === 'failure'){
          swal({
            icon: 'warning',
            title: this.result.status,
            text: this.result.message,
          })
        }else{
          swal({
            icon: 'success',
            title: "Success",
            text: this.result.message,
            // showConfirmButton: false,
            buttons: [false],
            timer: 2000
          })

          this.error = null;
          this.Updated = true;
          setTimeout(() => {
            this.router.navigate(['/rules']);
            },2000);
        }
   });
      }
    })

  }

  onSelect(technique_ids) {
    this.selectedTacticsItems = undefined;
    var tactics_tech_data = [];
    this.http.post<DataTablesResponse>(environment.api_url + "/rules/tactics", {"technique_ids":technique_ids}, {headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res => {
        this.result = res;
        for (const i in this.result.data.tactics) {
          for (const tactic_index in this.dropdownTacticsList) {
            if(this.result.data.tactics[i] == this.dropdownTacticsList[tactic_index].id){
              tactics_tech_data.push(this.dropdownTacticsList[tactic_index]);
            }
          }
        }
        this.selectedTacticsItems = tactics_tech_data;
    });
  }

  getStringConcatinated(array_object){
    //Join Array elements together to make a string of comma separated list
    let string_object = "";
    try{
      if (array_object.length>0){
        string_object = array_object[0];
        for (let index = 1; index < array_object.length; index++) {
          string_object = string_object+','+array_object[index];
        }
        return string_object
      }
    }
    catch(Error){
      return ""
    }
  }

  getAlertersDict(alerter_list){
      var alerters_array = [];

      for(const index in alerter_list){
          for(const i in this.dropdownAlertList){
              if(alerter_list[index]==this.dropdownAlertList[i]['value']){
                  alerters_array.push(this.dropdownAlertList[i]);
              }
          }
      }
      return alerters_array
  }

  getTacticsDict(tactic_list){
      var tactics_array = [];

      for(const index in tactic_list){
          for(const i in this.dropdownTacticsList){
              if(tactic_list[index]==this.dropdownTacticsList[i]['id']){
                  tactics_array.push(this.dropdownTacticsList[i]);
              }
          }
      }
      return tactics_array
  }

  OnRadioBtnChnge(arg) {
    if (arg == "DEFAULT") {
    this.model.rule_type = arg;
    this.mitre_show = false;
    }
    else if (arg == "MITRE") {
      this.mitre_show = true;
    }
    }
  goBack() {
    this._location.back();
  }
  resetForm() {
    // alert('test');
    this.ngOnInit()
    // this.updateRuleObj.pop();

   }
   onItemSelect(item:any){
     this.enableAddDescriptionEmail(true);
   }
   OnItemDeSelect(item:any){
     this.enableAddDescriptionEmail(true);
   }
   onSelectAll(items: any){
     this.enableAddDescriptionEmail(true);
   }
   onDeSelectAll(items: any){
     this.enableAddDescriptionEmail(false);
   }
   clickreset(){
     this.mitre_show=false
   }
   enableAddDescriptionEmail(isEnable){
     this.isEmailEnabled = false;
     if(isEnable){
       for (const i in this.selectedAlertItems) {
         if( this.selectedAlertItems[i].value == 'email' ){ this.isEmailEnabled = true; }
       }
     }
    }

   addDescriptionEmail(e){
      this.isAddDescriptionEmail = e.target.checked;
   }
   pagenotfound() {
     this.router.navigate(['/pagenotfound']);
   }
}
