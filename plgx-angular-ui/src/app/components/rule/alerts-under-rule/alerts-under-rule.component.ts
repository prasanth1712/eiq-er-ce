import { AfterViewInit,Component, OnInit,ViewChild ,} from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { DataTableDirective } from 'angular-datatables';
import { Subject } from 'rxjs';
import {HttpClient, HttpResponse} from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import {JsonEditorComponent, JsonEditorOptions} from 'ang-jsoneditor';
import {CommonapiService} from '../../../dashboard/_services/commonapi.service';
import { Location } from '@angular/common';
import { saveAs } from 'file-saver';
import swal from 'sweetalert';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}
@Component({
  selector: 'app-alerts-under-rule',
  templateUrl: './alerts-under-rule.component.html',
  styleUrls: ['./alerts-under-rule.component.css']
})
export class AlertsUnderRuleComponent implements AfterViewInit,OnInit {
  @ViewChild(JsonEditorComponent, {static: true}) editor: JsonEditorComponent;
  public editorOptions: JsonEditorOptions;
id:any;
@ViewChild(DataTableDirective, {static: false})
dtElement: DataTableDirective;
dtTrigger: Subject<any> = new Subject();
alert_data:any;
alerted_data_json:any;
// dtOptions: DataTables.Settings = {};
dtOptions:any = {}
searchText:string;
errorMessage:any;
toggle: boolean = false;
masterSelected:boolean;
checklist:any;
checkedList:any;
rule_name:string;
responsedata:any;
submitted = false;
verdict: any;
AlertId: any;
multipleSelect:boolean=false;
resolveAlertForm:FormGroup;
alert_selectedItem:any;
AggregatedId:any;
aggregated_data:any={};
aggregate_tab=[];
aggregatedOptions: any = {};
aggregateoutput:any;
aggregatelist:any;
dtTriggerAggregatedAlerts: Subject<any> = new Subject();
myjson: any = JSON;
aggregateTabLength:any;
  constructor(
    private _Activatedroute: ActivatedRoute,
    private http: HttpClient,
    private commonapi: CommonapiService,
    private router: Router,
    private _location: Location,
    private formBuilder: FormBuilder,
  ) { }

  ngOnInit() {
     this._Activatedroute.paramMap.subscribe(params => {
      this.id = params.get('id');
    })
    this.resolveAlertForm = this.formBuilder.group({
      comment: '',
      resolveAlert: ['', Validators.required],
    })
    this.rule_name=localStorage.getItem('rule_name')
    this.getAlert();
    this.GetAggregatedDataFilterWithQueryName(null);
  }

  getAlert(){
    var that=this;
    this.dtOptions = {
      pagingType: 'full_numbers',
      pageLength: 10,
      serverSide: true,
      processing: false,
      searching: true,
      destroy: true,
      dom: '<"pull-right"B><"pull-right"f><"pull-left"l>tip',
      buttons: [
        {
          text: 'Export',
          action: function ( e, dt, node, config ) {
            that.exportAlerts(that.id);
          },
          className: 'export_button'
        }
      ],
      "language": {
        "search": "Search: "
      },
      ajax: (dataTablesParameters: any,callback) => {

        var body = dataTablesParameters;
        body['limit']=body['length'];
        if(body.search.value!= ""  &&  body.search.value.length>=1)
      {

        body['searchterm']=body.search.value;

      }
        if(body['searchterm']==undefined){
          body['searchterm']="";
        }
       body["rule_id"]=this.id
        this.http.post<DataTablesResponse>(environment.api_url + "/alerts", body, {
          headers: {
            'Content-Type': 'application/json',
            'x-access-token': localStorage.getItem('token')
          }
        }).subscribe(res => {
          this.responsedata = res;
          if(this.responsedata.status == "failure"){
            this.pagenotfound();
          }
          else{
          this.alert_data =res.data['results'];
        if(res.data['count'] > 0 && res.data['results'] != undefined)
        {
          this.checklist = [ ];
          this.masterSelected = false;
          for (const i in this.alert_data){
            let checkboxdata={}
            checkboxdata['id']=this.alert_data[i].id
            checkboxdata['isSelected']=false
              this.checklist.push(checkboxdata)
          }
          $('.dataTables_paginate').show();
          $('.dataTables_info').show();
          $('.dataTables_filter').show()
        }
        else{
          if(body.search.value=="" || body.search.value == undefined)
          {
            this.errorMessage="No Records Found";
          }
          else{
            this.errorMessage="No Matching Record Found";
          }
          $('.dataTables_paginate').hide();
          $('.dataTables_info').hide();

        }
          callback({
            recordsTotal: res.data['total_count'],
            recordsFiltered: res.data['count'],
            data: []
          });
        }
        });
      },
      ordering: false,
      columns: [{data: 'hostname'}]
    }
  }

  get f() { return this.resolveAlertForm.controls; }
  ngAfterViewInit(): void {
    this.dtTrigger.next();
  }
  ngOnDestroy(): void {
    this.dtTrigger.unsubscribe();
  }
    /*  Alerted Entry Json Editor Start*/
    showdata(any, title) {
      this.toggle = false;
      setTimeout(() => {
        this.editorOptions = new JsonEditorOptions();
        this.editorOptions.mode = 'view';
        this.alerted_data_json = any;
        this.toggle = true;
      }, 100);
    }
    onItemChange(value){
      this.verdict = value;
    }
    resolveAlert(alertId,selectOption) {
      this.AlertId = alertId;
      this.multipleSelect = selectOption;
      this.openResolveAlert();
    }
    multiResolveAlert(selectOption) {
      this.multipleSelect = selectOption
      this.openResolveAlert();
    }
    openResolveAlert(){
      let modal = document.getElementById("resolveAlertModal");
      modal.style.display = "block";
    }
    closeResolveAlert(){
      this.submitted = false;
      this.resolveAlertForm.reset()
      let modal = document.getElementById("resolveAlertModal");
      modal.style.display = "none";
    }
    /*  Alerted Entry Json Editor End*/

      /* Start Resolve alert*/
      resolveAlertSubmitForm(){
        this.submitted = true;
        let resolveAlertsData={}
        resolveAlertsData["resolve"]=true;

        if(this.multipleSelect == false){   resolveAlertsData['alert_ids']=this.AlertId;     }
        else{ resolveAlertsData['alert_ids']= this.checkedList; }

        if(this.verdict == 'True Positive'){
          resolveAlertsData['verdict'] = true;
        }
        else if(this.verdict == 'False Positive'){
          resolveAlertsData['verdict'] = false;
        }
        resolveAlertsData['comment'] = this.f.comment.value;
        // stop here if form is invalid
        if (this.resolveAlertForm.invalid) {
            return;
        }
        this.commonapi.AlertsResolve(resolveAlertsData).subscribe(res => {
          if (res['status'] == "success") {
            let modal = document.getElementById("resolveAlertModal");
            modal.style.display = "none";
            swal({
              icon: 'success',
              title: 'Resolved',
              text: 'Alert has been successfully resolved',
              buttons: [false],
              timer: 3000
            })
          } else {
            swal({
              icon: "warning",
              text: res['message'],
            })
          }
          setTimeout(() => {
            this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
              // Destroy the table first
              dtInstance.destroy();
              // Call the dtTrigger to rerender again
              this.dtTrigger.next();
            });
          }, 2000);
        })
      }
      /* END Resolve alert*/
      goBack() {
        this._location.back();
      }
      checkUncheckAll() {
        for (var i = 0; i < this.checklist.length; i++) {
          this.checklist[i].isSelected = this.masterSelected;
        }
        this.getCheckedItemList();
      }
      isAllSelected() {
        this.masterSelected = this.checklist.every(function(item:any) {
            return item.isSelected == true;
          })
        this.getCheckedItemList();
      }

      getCheckedItemList(){
        this.checkedList = [];
        for (var i = 0; i < this.checklist.length; i++) {
          if(this.checklist[i].isSelected)
          this.checkedList.push(this.checklist[i].id);
        }
      }
get_csv_data(id){
  var payloadDict={"source":'rule',"rule_id":id}
    this.commonapi.rule_alerts_export(payloadDict).subscribe(blob => {
    saveAs(blob,"alert"+"_"+"rule"+'.csv');
  })
}


/*  Export csv file for all the alert type*/
exportAlerts(id){
var payloadDict = {"source":'rule',"rule_id":id}
var alert_name = JSON.stringify(payloadDict);
var token_val = localStorage.getItem('token');
var today = new Date();
var currentDate = today.getDate()+"-"+(today.getMonth()+1)+"-"+today.getFullYear();
$.ajax({
    "url": environment.api_url+"/alerts/alert_source/export",
    "type": 'POST',
    "data": alert_name,
    headers: {
        "content-type":"application/json",
        "x-access-token": token_val
      },
    "success": function(res, status, xhr) {
      if(res.status == 'failure'){
        var csvData = new Blob([res.message], {
            type: 'text/csv;charset=utf-8;'
        });
        var csvURL = window.URL.createObjectURL(csvData);
        var tempLink = document.createElement('a');
        tempLink.href = csvURL;
        tempLink.setAttribute('download', 'alert'+'_'+payloadDict.source+ '_' + currentDate + '.csv');
        tempLink.click();
      }
      else{
        var csvData = new Blob([res], {
            type: 'text/csv;charset=utf-8;'
        });
        var csvURL = window.URL.createObjectURL(csvData);
        var tempLink = document.createElement('a');
        tempLink.href = csvURL;
        tempLink.setAttribute('download', 'alert'+'_'+payloadDict.source+ '_' + currentDate + '.csv');
        tempLink.click();
    }
      }

});
return false;
}

// Start Aggregated alerts
getAlertsAggregatedData(id){
  this.AggregatedId = id;
  this.aggregated_data = [];
  $('.aggregated_table_data').hide();
  this.commonapi.get_alerts_aggregated_data(id).subscribe((res: any) => {
    $('.aggregation_loader').hide();
    this.aggregateTabLength=res.data.length
   for(const i in res.data){
     this.aggregated_data.push(res.data[i].query_name)
    }
    if(this.aggregated_data!=0){
      this.GetAggregatedDataFilterWithQueryName(this.aggregated_data[0]);
    }else{

    }
  })
}

GetAggregatedDataFilterWithQueryName(name){
  this.dtTriggerAggregatedAlerts.next();
  $('.aggregated_table_data').show();
  var that=this;
  this.alert_selectedItem = name;
  this.aggregatedOptions = {
    pagingType: 'full_numbers',
    pageLength: 10,
    serverSide: true,
    processing: true,
    searching: true,
    dom: '<"pull-right"B><"pull-right"f><"pull-left"l>tip',
    buttons: [
      {
        text: 'Export',
        attr:  {id: 'IdExport'},
        action: function ( e, dt, node, config ) {
          that.exportAggregatedData();
        },
      },
    ],
    destroy:true,
    "language": {
      "search": "Search: "
    },
    ajax: (dataTablesParameters: any, callback) => {
      var body = dataTablesParameters;
      var searchitem = '';
      if(body.search.value!= ""  &&  body.search.value.length>=3){
        searchitem=body.search.value;
      }
      if(body.search.value!="" && body.search.value.length<3){
       return;
      }
      var payload = {
	          "query_name":this.alert_selectedItem,
	          "start":body['start'],
            "limit":body['length'],
            "searchterm":searchitem,
      }
      this.http.post<DataTablesResponse>(environment.api_url+"/alerts/"+this.AggregatedId+"/alerted_events", payload, { headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res =>{
        this.aggregateoutput = res;
        this.aggregatelist = this.aggregateoutput.data.results;
        if(this.aggregatelist.length >0 &&  this.aggregatelist!=undefined)
        {
          $('.dataTables_paginate').show();
          $('.dataTables_info').show();
        }
        else{
          if(body.search.value=="" || body.search.value == undefined){
            this.errorMessage="No Data Found";
          }
          else{
            this.errorMessage="No Matching Record Found";
          }
          $('.dataTables_paginate').hide();
          $('.dataTables_info').hide();
        }
        callback({
          recordsTotal: this.aggregateoutput.data.count,
          recordsFiltered: this.aggregateoutput.data.count,
          data: []
        });
      });
    },

    ordering: false,
  }
}
exportAggregatedData(){
  var queryName = this.alert_selectedItem;
  var alertId = this.AggregatedId;
  var today = new Date();
  var currentDate = today.getDate()+"-"+(today.getMonth()+1)+"-"+today.getFullYear();
  this.commonapi.alertedEventsExport(alertId,queryName).subscribe((res: any) => {
    saveAs(res,  'alert'+'_'+this.alert_selectedItem+ '_' + currentDate + '.csv');
  })
}

pagenotfound() {
    this.router.navigate(['/pagenotfound']);
}
}
