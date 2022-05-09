import {AfterViewInit, Component, OnDestroy, OnInit, QueryList, ViewChild, ViewChildren} from '@angular/core';
import {DataTablesModule} from 'angular-datatables';
import {DataTableDirective} from 'angular-datatables';
import {Subject} from 'rxjs';
import {HttpClient, HttpResponse} from '@angular/common/http';
import {CommonapiService} from '../../dashboard/_services/commonapi.service';
import {JsonEditorComponent, JsonEditorOptions} from 'ang-jsoneditor';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

import {environment} from '../../../environments/environment';
import {Router, ActivatedRoute} from '@angular/router';
import '../../../assets/vendors/timeline/lib/timeline.js';
import '../../../assets/vendors/timeline/lib/timeline-locales.js';
import {NgDatepickerModule, DatepickerOptions} from 'ng2-datepicker';
import {NgModule} from '@angular/core';
import { Location, DatePipe } from '@angular/common';
import {NgbDateStruct,NgbDate, NgbCalendar,NgbInputDatepickerConfig} from '@ng-bootstrap/ng-bootstrap';
declare var links: any;
import swal from 'sweetalert';
import {moment} from "vis-timeline";
import {saveAs} from 'file-saver';
class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}


@Component({
  selector: 'app-alerts',
  templateUrl: './alerts.component.html',
  styleUrls: ['./alerts.component.css', './alerts.component.scss'],
  providers: [DatePipe]
})
@NgModule({
  imports: [
    NgDatepickerModule, DatePipe
  ],

})

export class AlertsComponent implements AfterViewInit, OnDestroy, OnInit {
  @ViewChild(JsonEditorComponent, {static: true}) editor: JsonEditorComponent;
  selectedDate = {};
  public editorOptions: JsonEditorOptions;
  alertSource: any;
  options = {};
  datepicker_date = {};
  virusTotalCount: number;
  alert_data:any;
  IBMForceTotalCount: number;
  AlientTotalVault: number;
  IOCTotalCount: number;
  RuleTotalCount: number;
  alertSourceData = {};
  alerted_data_json: any;
  alert_title: any;
  errorMessage= {  };
  all_options = {};
  title = 'Angular 7 CheckBox Select/ Unselect All';
  masterSelected = {};
  checklist = {};
  checkedList = {};
  fetched = {};
  dtTrigger: Subject<any>[] = [];
  events_ids = [];
  @ViewChildren(DataTableDirective)
  dtElements: QueryList<DataTableDirective>;
  activeAlerts: any;
  purge_data_duration:any;
  submitted = false;
  verdict: any;
  AlertId: any;
  source: any;
  multipleSelect:boolean=false;
  resolveAlertForm:FormGroup;
  alert_selectedItem:any;
  aggregated_data:any={};
  aggregate_tab=[];
  aggregatedOptions: any = {};
  id: any;
  aggregateoutput:any;
  aggregatelist:any;
  dtTriggerAggregatedAlerts: Subject<any> = new Subject();
  myjson: any = JSON;
  aggregateTabLength:any;
  isAlertSelected:boolean = false;
  constructor(
    private commonapi: CommonapiService,
    private http: HttpClient,
    private _Activatedroute: ActivatedRoute,
    private _location: Location,
    private calendar: NgbCalendar,
    private config: NgbInputDatepickerConfig,
    private formBuilder: FormBuilder,
    private datePipe: DatePipe,
  ) {
  }

  toggle: boolean = false;

  ngOnInit() {

    $.fn.dataTable.ext.errMode = 'none';
    this._Activatedroute.params.subscribe(params => {

      this.activeAlerts = this._Activatedroute.snapshot.queryParams["id"];
      if(this.activeAlerts!=undefined){
      window.history.replaceState("object or string", "Title", "/"+window.location.href.substring(window.location.href.lastIndexOf('/') + 1).split("?")[0]);
      }
    });
    this.resolveAlertForm = this.formBuilder.group({
      comment: '',
      resolveAlert: ['', Validators.required],
    })
    $('#hidden_button').bind('click', (event, source, event_ids) => {
      this.toggleDisplay(source, event_ids);
    });
    this.get_Platform_settings();
    this.commonapi.alerts_source_count_api().subscribe((res: any) => {
      var alerttype = ['rule', 'virustotal','ioc', 'alienvault', 'ibmxforce']
      var sort_alert_type = []
      for (const name in alerttype) {
        for (const alert in res.data.alert_source) {

          if (alerttype[name] == res.data.alert_source[alert].name) {
            sort_alert_type.push(res.data.alert_source[alert]);
          }
        }
      }
      this.alertSource = sort_alert_type;
      var active_souce=this.alertSource[0].name;
      if (this.activeAlerts != null && this.activeAlerts != '' && this.activeAlerts != undefined &&  this.alertSource.find(x => x.name == this.activeAlerts)!=undefined) {
        active_souce = this.alertSource.find(x => x.name == this.activeAlerts).name;
      }
      if (this.alertSource.length > 0) {


        for (let i = 0; i < this.alertSource.length; i++) {

          if (this.alertSource[i].name == "virustotal") {
            this.virusTotalCount = this.alertSource[i].count;
          }
          if (this.alertSource[i].name == "ibmxforce") {
            this.IBMForceTotalCount = this.alertSource[i].count;
          }
          if (this.alertSource[i].name == "alienvault") {
            this.AlientTotalVault = this.alertSource[i].count;
          }
          if (this.alertSource[i].name == "ioc") {
            this.IOCTotalCount = this.alertSource[i].count;
          }
          if (this.alertSource[i].name == "rule") {
            this.RuleTotalCount = this.alertSource[i].count;
          }
        }
      }


      for (let i = 0; i < this.alertSource.length; i++) {

          this.getAlertData(this.alertSource[i].name);


      }
      setTimeout(() => {

        this.show_hide_div(active_souce);
      }, 300);


    })
    this.GetAggregatedDataFilterWithQueryName(null);
  }
  validDateFormat(value) {
    if(value) {
      let date = value.substring(0, 10);
      let time = value.substring(11, 19);
      let millisecond = value.substring(20)
      let date1 = date.split('-')[0];
      let date2 = date.split('-')[1];
      let date3 = date.split('-')[2];
      let validDate = date3+'-'+date2+'-'+date1 + ' ' + time;
      return validDate
    }

    return null;

  }

  get_options(source) {
    var that=this;

    return {
      pagingType: 'full_numbers',
      pageLength: 10,
      serverSide: true,
      processing: true,
      searching: true,
      InfoPostFix:false,
      InfoFiltered:false,
      dom: '<"pull-right"B><"pull-right"f><"pull-left"l>tip',
      buttons: [
        {
          text: 'Export',
          action: function ( e, dt, node, config ) {
            that.exportAlerts(source);
          }
        }
      ],

      "language": {
        "search": "Search: ",
        "sInfoFiltered": "",
      },
      // "oLanguage": {
      //          "sInfoFiltered": "",
      //       },
      ajax: (dataTablesParameters: any, callback) => {
        var body = dataTablesParameters;
        body['limit'] = body['length'];
        body['source'] = source;
        var searching=false;
        if (body.search.value != "" && body.search.value.length >= 1) {
          body['searchterm'] = body.search.value;
          searching=true;
        }

        if (this.events_ids.length > 0) {
          body['event_ids'] = this.events_ids;

        }

        var duration = $('#duration_' + source).val();

        var type = $('#type_' + source).val();


        // var date = this.datepicker_date[source];
        var selectedDate = this.selectedDate[source];
        var date = selectedDate.year + '-' + selectedDate.month + '-' + selectedDate.day;
        // if(date instanceof Date){
        //   date=this.convertDate(date);
        // }
        body['type']=type;
        body['duration']=duration;


        if (body['searchterm'] == undefined) {
            body['searchterm'] = "";
        }

        body['date']=date;


        this.http.post<DataTablesResponse>(environment.api_url + "/alerts", body, {
          headers: {
            'Content-Type': 'application/json',
            'x-access-token': localStorage.getItem('token')
          }
        }).subscribe(res => {
          this.checklist[source] = [];
          if(res.data.hasOwnProperty("total_count")){
          if (source == "virustotal") {
            this.virusTotalCount = res.data['total_count'];
          }
          if (source == "ibmxforce") {
            this.IBMForceTotalCount = res.data['total_count'];
          }
          if (source == "alienvault") {
            this.AlientTotalVault = res.data['total_count'];
          }
          if (source == "ioc") {
            this.IOCTotalCount = res.data['total_count'];
          }
          if (source == "rule" ) {
            this.RuleTotalCount = res.data['total_count'];
          }
          }
          if (res.data['count'] > 0 && res.data['results'] != undefined) {
            this.alertSourceData[source] = res.data['results'];
            this.masterSelected[source] = false;
            for (const i in this.alertSourceData[source]) {
              let checkboxdata = {}
              checkboxdata['id'] = this.alertSourceData[source][i].id;
              checkboxdata['isSelected'] = false
              this.checklist[source].push(checkboxdata);
            }
            this.getCheckedItemList(source);

            // $("#DataTables_Table_0_info").
            $('#'+source+'_table_paginate').show();
            $('#'+source+'_table_info').show();


            this.errorMessage[source] = ''
          } else {

            if (!searching) {
              if((source == "virustotal" && this.virusTotalCount > 0 )
                 || (source == "ibmxforce" && this.IBMForceTotalCount > 0 )
                 || (source == "alienvault" && this.AlientTotalVault > 0 )
                 || (source == "ioc" && this.IOCTotalCount > 0 )
                 || (source == "rule" && this.RuleTotalCount > 0 )
                ){
                this.errorMessage[source] = "No alerts found for the selected duration";
              }
              else{
                this.errorMessage[source] = "No alerts found";
              }


              $('#'+source+'_table_paginate').hide();
              $('#'+source+'_table_info').hide();
            } else {
              this.errorMessage[source] = "No Data";
              $('#'+source+'_table_paginate').hide();
              $('#'+source+'_table_info').hide();
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
      columns: [{data: 'hostname'}]
    }
  }

  getAlertData(source) {
    var today = new Date();
    if(this.dtTrigger[source] == undefined) {
      this.dtTrigger[source] = new Subject<any>();
      this.selectedDate[source] = this.calendar.getToday();
      // this.datepicker_date[source]=today;
    }

    this.all_options[source] = this.get_options(source);


  }

  ngAfterViewInit(): void {
  }

  ngOnDestroy(): void {
  }

  /*  Alerted Entry Json Editor Start*/
  showdata(any, title) {
    this.alert_title = title;

    this.toggle = false;
    setTimeout(() => {
      this.editorOptions = new JsonEditorOptions();
      this.editorOptions.mode = 'view';
      this.alerted_data_json = any;
      this.toggle = true;
    }, 100);
  }

  /*  Alerted Entry Json Editor End*/
  checkUncheckAll(source) {
    for (var i = 0; i < this.checklist[source].length; i++) {
      this.checklist[source][i].isSelected = this.masterSelected[source];
    }
    this.getCheckedItemList(source);
  }

  isAllSelected(source) {
    this.masterSelected[source] = this.checklist[source].every(function (item: any) {
      return item.isSelected == true;
    })
    this.getCheckedItemList(source);
  }

  getCheckedItemList(source) {
    this.checkedList[source] = [];
    for (var i = 0; i < this.checklist[source].length; i++) {
      if (this.checklist[source][i].isSelected)
        this.checkedList[source].push(this.checklist[source][i].id);
    }
  }

  resolveAlert(alertId, source) {
    this.AlertId = alertId;
    this.source = source;
    this.openResolveAlert();
  }
  multiResolveAlert(source,selectOption) {
    this.isAlertSelected = false;
    this.checklist[source].forEach((value) => {
      if(value.isSelected == true){this.isAlertSelected = true}
    });
    this.source = source;
    this.multipleSelect = selectOption;
    if(this.isAlertSelected){
      this.openResolveAlert();
    }
    else{
      swal({
        icon: "warning",
        text: "Please Select Alert",
      })
    }

  }
  openResolveAlert(){
    let modal = document.getElementById("resolveAlertModal");
    modal.style.display = "block";
  }
  onItemChange(value){
    console.log(value);
    this.verdict = value;
  }
  resolveAlertSubmitForm(){
    this.submitted = true;
    let resolveAlertsData={}
    resolveAlertsData["resolve"]=true

    if(this.multipleSelect == false){   resolveAlertsData['alert_ids']=this.AlertId;     }
    else{ resolveAlertsData['alert_ids']= this.checkedList[this.source]; }

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
        this.dtTrigger[this.source].next();
      }, 2000);
    })
  }
  closeResolveAlert(){
    this.submitted = false;
    this.resolveAlertForm.reset()
    let modal = document.getElementById("resolveAlertModal");
    modal.style.display = "none";
  }
  get f() { return this.resolveAlertForm.controls; }
  resolvedAllSelected(source) {
    let resolve_alerts_data={}
    resolve_alerts_data["resolve"]=true
    resolve_alerts_data['alert_ids']=this.checkedList[source]
    if (this.checkedList[source].length == 0) {
    }
    else {
    swal({
        title: 'Are you sure?',
        text: "Want to resolve the alerts!",
        icon: 'warning',
        buttons: ["Cancel", "Yes,Resolve"],
        dangerMode: true,
        closeOnClickOutside: false,
      }).then((willDelete) => {
        if (willDelete) {
            this.commonapi.AlertsResolve(resolve_alerts_data).subscribe(res => {
              if (res['status'] == "success") {
                 swal({
                  icon: 'success',
                  title: 'Resolved',
                  text: 'Alerts has been successfully resolved',
                  buttons: [false],
                  timer: 2000
                })
                }
               else {
                swal({
                  icon: "warning",
                  text: res['message'],
                })
              }
          })
          setTimeout(() => {
            this.dtTrigger[source].next();
          }, 3000);
          }
        })
    }
    }

  toggleDisplay(source, events) {
    this.events_ids = events;
    this.dtTrigger[source].next();
  }

  show_hide_div(name: any) {
    // this.dtTrigger[name].next();
    this.events_ids=[];
    $('.nav-link-active').removeClass("active");
    $('#' + name).addClass("active");
    $('.alert_source_div').hide();
    $('#div_' + name).show();
    $('.no_data').hide();

    if (this.fetched[name] != true) {
      this.toggleDisplay(name, []);
    }
    this.alert_data ={"source":name};
  }



  myHandler( source: any) {
    this.events_ids=[];
    setTimeout(() => {

    var duration = $('#duration_' + source).val();

    var type = $('#type_' + source).val();

  this.grabNewDataBasedOnDate(source, duration, type);
    this.dtTrigger[source].next();
  },400);
  }

  grabNewDataBasedOnDate(source, duration, type) {
    this.getAlertData(source);
  }

  convert(str) {
    var date = new Date(str),
      mnth = ("0" + (date.getMonth() + 1)).slice(-2),
      day = ("0" + date.getDate()).slice(-2);
    return [date.getFullYear(), mnth, day].join("-");
  }

  convertDate(date) {
    var  mnth = ("0" + (date.getMonth() + 1)).slice(-2),
      day = ("0" + date.getDate()).slice(-2);
    return [date.getFullYear(), mnth, day].join("-");
  }

  update_graph(source: any) {
    this.myHandler( source);
  }

    /*  Export csv file for all the alert type*/
  exportAlerts(source){
    var selectedDate = this.selectedDate[source];
    var date = selectedDate.year + '-' + selectedDate.month + '-' + selectedDate.day;
    // var payloadDict = {"source": source, "duration": $('#duration_' + source).val(), "type": $('#type_' + source).val(), "date":this.convertDate(this.datepicker_date[source])}
    var payloadDict = {"source": source, "duration": $('#duration_' + source).val(), "type": $('#type_' + source).val(), "date":date}
    console.log(payloadDict);
    if (this.events_ids.length > 0) {
      payloadDict['event_ids'] =this.events_ids;
    }
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
  this.id = id;
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
      this.http.post<DataTablesResponse>(environment.api_url+"/alerts/"+this.id+"/alerted_events", payload, { headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res =>{
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
    columns: [{ data: 'line' }, { data: 'message' }, { data: 'severity' }, { data: 'filename' },{ data: 'created' },{ data: 'version' }]
  }
}
exportAggregatedData(){
  var queryName = this.alert_selectedItem;
  var alertId = this.id;
  var today = new Date();
  var currentDate = today.getDate()+"-"+(today.getMonth()+1)+"-"+today.getFullYear();
  this.commonapi.alertedEventsExport(alertId,queryName).subscribe((res: any) => {
    saveAs(res,  'alert'+'_'+this.alert_selectedItem+ '_' + currentDate + '.csv');
  })
}


get_Platform_settings(){
  this.commonapi.getConfigurationSettings().subscribe(res => {
    this.purge_data_duration=res.data.purge_data_duration;
  });
}
Get_total_alerts_based_on_alert_type(name){
  $(".timeline-event-dot").removeClass("selected")
  this.events_ids=[];
  this.dtTrigger[name].next();
}

goBack(){
  this._location.back();
}
}
