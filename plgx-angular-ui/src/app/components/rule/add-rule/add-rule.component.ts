import { Component, OnInit } from '@angular/core';
import {CommonapiService} from '../../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../../dashboard/_services/commonvariable.service';
import { FormGroup, FormBuilder, FormArray, Validators, FormControl } from '@angular/forms';
import { QueryBuilderConfig, QueryBuilderComponent, QueryBuilderClassNames } from 'angular2-query-builder';
import { first } from 'rxjs/operators';
import swal from 'sweetalert';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
import { environment } from '../../../../environments/environment'
import { HttpClient, HttpResponse } from '@angular/common/http';
import { Title } from '@angular/platform-browser';

declare  function init_querybuilder(): any;

class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}
@Component({
  selector: 'app-add-rule',
  templateUrl: './add-rule.component.html',
  styleUrls: ['./add-rule.component.css']
})

export class AddRuleComponent implements OnInit {
  addRule: FormGroup;
  submitted = false;
  error:any;
  Updated:any;
  public result:any;
  public addRuleObj: any = {
    type:"MITRE",
    status:"ACTIVE",
    severity:"INFO",
    tactics:[]
  }
  mitre_show:any;
  type_selected:any;
  token_value:any;
  data: any[];
  add_result:any;
  query_builder:any;
  dropdownAlertList = [];
  selectedAlertItems = [];
  dropdownAlertSettings = {};
  selected_alerts :any =[];

  dropdownTacticsList = [];
  selectedTacticsItems = [];
  dropdownTacticsSettings = {};
  isEmailEnabled = false;
  isAddDescriptionEmail = false;
  constructor(
    private commonapi: CommonapiService,
    private commonvariable: CommonVariableService,
    private fb:FormBuilder,
    private router: Router,
    private _location: Location,
    private http: HttpClient,
    private titleService: Title,

  ) { this.type_selected = 'DEFAULT';
  this.addRule= this.fb.group({
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

  })
}

  ngOnInit() {
    this.addRuleObj.platform = 'all';
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Add rule");

    init_querybuilder();
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
      {"id":1,"itemName":"Rsyslog", "value":"rsyslog"},
      {"id":2,"itemName":"Email", "value":"email"}
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

  }

  get f() { return this.addRule.controls; }

  onSubmit(){
    this.submitted = true;
    if (this.addRule.invalid) {
        return;
    }
    this.token_value = localStorage.getItem('token');
    $(document).ready(() => {
      this.query_builder = $('#rules-hidden').val();
      let selected_alerts = this.f.alerters.value;
      let selected_tactics = this.f.tactics.value;
      this.addRuleObj={
        "name":this.f.name.value,
        "description":this.f.description.value,
        "status":this.f.status.value,
        "severity":this.f.severity.value,
        "platform":this.f.platform.value,
        "type":this.f.rule_type.value,
        "technique_id":this.f.technique_id.value,
        "alert_description":this.isAddDescriptionEmail
      }
      if(this.addRuleObj.status==null){
        this.addRuleObj['status']="ACTIVE"
      }
      if(this.addRuleObj.severity==null){
        this.addRuleObj['severity']="INFO"
      }
      if(this.addRuleObj.type==null){
        this.addRuleObj['type']="DEFAULT"
      }
      var alerters_array = [];
      var tactics_array = [];

      for(const index in selected_alerts){
          alerters_array.push(selected_alerts[index]['value']);
      }

      for(const index in selected_tactics){
          tactics_array.push(selected_tactics[index]['id']);
      }
      this.addRuleObj["alerters"] = this.getStringConcatinated(alerters_array);
      this.addRuleObj["tactics"] = this.getStringConcatinated(tactics_array);
      this.addRuleObj["conditions"]= JSON.parse(this.query_builder);
      console.log("rule obj is",this.addRuleObj);
      this.http.post<DataTablesResponse>(environment.api_url + "/rules/add", this.addRuleObj, {headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res => {

        this.result=res;
        if(this.result && this.result.status === 'failure'){
          swal({
            icon: 'warning',
            title: 'Failure',
            text: this.result.message,
          })
        }else{
          swal({
            icon: 'success',
            title: 'Success',
            text: this.result.message,
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
  })
  }

  onChangeTechniqueID(technique_ids) {
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
  goBack(){
    this._location.back();
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
}
