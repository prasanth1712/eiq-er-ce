import { Component, OnInit } from '@angular/core';
import { CommonapiService } from '../../dashboard/_services/commonapi.service';
import { ConditionalExpr } from '@angular/compiler';
import { Router, ActivatedRoute, ParamMap } from '@angular/router';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Subject, Subscription } from 'rxjs';
import { AuthorizationService } from '../../dashboard/_services/Authorization.service';
class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}
@Component({
  selector: 'app-rule',
  templateUrl: './rule.component.html',
  styleUrls: ['./rule.component.css','./rule.component.scss']
})
export class RuleComponent implements OnInit {
  public rule: any;
  public ruledata:any;
  public ruleid:any;
  public rule_condition:any;
  public rules:any = [];
  public conditions:any = {};
  searchText:any;
  show=false;
  selectedItem:any;
  public ruleAlert :any = [];
  public ruleAlertVal :any = [];
  public tacticsAlert :any =[];
  public ruleTacticsVal :any =[];
  conditionLenght: any
  role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess}

  constructor(
    private commonapi: CommonapiService,
    private router: Router,
    private http: HttpClient,
    private authorizationService: AuthorizationService,
  ) { }

getById(event, newValue,rule_id){
  this.selectedItem = newValue;
  console.log(newValue,rule_id)
  this.ruleid = rule_id;
  this.ruleAlertVal = [];
  // this.rule_alert1 = [];
  this.ruleTacticsVal = [];
  this.tacticsAlert = [];
   for(const i in this.rule.data.results){
        if (this.rule.data.results[i].id == this.ruleid){
          this.ruledata =this.rule.data.results[i];
          this.ruleAlertVal = this.getStringConcatinated(this.rule.data.results[i].alerters);
          this.rule_condition = this.ruledata.conditions.condition;
          this.rules = this.ruledata.conditions.rules;
          this.conditions = this.ruledata.conditions;
          this.ruleTacticsVal = this.getStringConcatinated(this.rule.data.results[i].tactics);
  }
  }
  localStorage.setItem('rule_name',this.ruledata.name);
 }

 getfirst_data(firstdata){
  this.ruledata =firstdata;
  this.ruleid=this.ruledata.id;
  this.selectedItem = this.ruledata.name;
  this.conditions = this.ruledata.conditions;
  this.rule_condition = this.ruledata.conditions.condition;
  this.rules = this.ruledata.conditions.rules;
  this.ruleAlertVal = [];
  this.ruleTacticsVal = [];
  this.tacticsAlert = []
   for(const i in this.rule.data.results){
      if (this.rule.data.results[i].id == this.ruleid){
        this.ruledata =this.rule.data.results[i];
        this.ruleAlertVal = this.getStringConcatinated(this.rule.data.results[i].alerters);
        this.ruleTacticsVal = this.getStringConcatinated(this.rule.data.results[i].tactics);
  }
  localStorage.setItem('rule_name',this.ruledata.name);
  }
  this.conditionLenght = this.conditions.rules.length
}
  ngOnInit() {
     this.getRuleList();
  }

ruleList:any;
errorMessage:any;
sortedRuleDataNameId = [];
dtOptions: DataTables.Settings = {};
dtTrigger: Subject<any> = new Subject();
getRuleList(){
  this.dtOptions = {
    pagingType: 'full_numbers',
    pageLength: 10,
    serverSide: true,
    processing: true,
    searching: true,
    lengthChange: false,
    info:false,
    scrollCollapse: true,
    "language": {
      "search": "Search: "
    },
    ajax: (dataTablesParameters: any,callback) => {
      var body = dataTablesParameters;
      body['limit']=body['length'];
      if(body.search.value!= ""  &&  body.search.value.length>=1){
         body['searchterm']=body.search.value;
      }
      if(body['searchterm']==undefined){
          body['searchterm']="";
      }

      this.http.post<DataTablesResponse>(environment.api_url+"/rules", body,{ headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res =>{
      this.ruleList = res.data['results'];
      if(this.ruleList.length >0 &&  this.ruleList!=undefined){
        this.ruleList = res.data['results'];
        this.ruleList.sort((x,y) => y.name - x.name)
        $('.dataTables_paginate').show();
        this.rule = res;
        this.sortedRuleDataNameId=[];
        let name_and_percentage=[]
        $('.rule_body2').hide();
        $('.rule_body').show();
        for (const i in this.rule.data.results){
          name_and_percentage=[]
          name_and_percentage.push(this.rule.data.results[i].name)
          var d =  Math.pow(10,10);
          if(this.rule.data.total_alerts>0){
              var num=Number((Math.round((this.rule.data.results[i].alerts_count*100/this.rule.data.total_alerts) * d) / d).toFixed(1))
              name_and_percentage.push(num)
          }else{
               name_and_percentage.push(0)
          }
          name_and_percentage.push(this.rule.data.results[i].id)
          this.sortedRuleDataNameId.push(name_and_percentage)
        }
        this.getfirst_data(this.rule.data.results[0]);

      }else{
        if(body.search.value=="" || body.search.value == undefined){
          this.errorMessage = "No results found";
          $('.dataTables_paginate').hide();
        }
        else{
          this.errorMessage = "No search results found";
          $('.dataTables_paginate').hide();
        }
      }
        callback({
          recordsTotal: res.data['total_count'],
          recordsFiltered: res.data['count'],
          data: []
        });
      });
    },
    ordering: false,
    columns: [{data: 'Rule' }]
  }
}

ngAfterViewInit(): void {
  this.dtTrigger.next();
}

showShortDesciption = true

alterDescriptionText() {
   this.showShortDesciption = !this.showShortDesciption
}

getStringConcatinated(array_object){
  //Join Array elements together to make a string of comma separated list
  let string_object = "";
  try{
    if (array_object.length>0){
      string_object = array_object[0];
      for (let index = 1; index < array_object.length; index++) {
        string_object = string_object+', '+array_object[index];
      }
      return string_object
    }
  }
  catch(Error){
    return ""
  }
}


getRulesArray(ListObject, MainArray){
    for(const i in ListObject){
      if('condition' in ListObject[i]){
        MainArray.push({'condition':ListObject[i]['condition'], 'rules':this.getRulesArray(ListObject[i].rules, [])});
      }else
      {
        var dict = {};
        for (let key in ListObject[i]) {
          let value = ListObject[i][key];
          dict[key] = value;
        }
        MainArray.push(dict);
      }
    }
    return MainArray
}

isString(argument){
  if(typeof(argument)==typeof('')){
    return true
  }else{
    return false
  }
}
}
