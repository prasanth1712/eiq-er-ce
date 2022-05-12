import {AfterViewInit, Component, OnDestroy, OnInit, QueryList, ViewChild, ViewChildren} from '@angular/core';
import {DataTableDirective} from 'angular-datatables';
import {Subject} from 'rxjs';
import {HttpClient, HttpResponse} from '@angular/common/http';
import {CommonapiService} from '../../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../../dashboard/_services/commonvariable.service';
import {JsonEditorComponent, JsonEditorOptions} from 'ang-jsoneditor';
import {Datatablecolumndefs} from '../../../dashboard/_helpers/datatable-columndefs';
import {environment} from '../../../../environments/environment';
import { Title } from '@angular/platform-browser';
import swal from 'sweetalert'
declare var $: any;
import 'datatables.net';

class AggregatedDataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltereds: number;
  recordsTotals: number;
}
class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}
@Component({
  selector: 'app-resolved-alerts',
  templateUrl: './resolved-alerts.component.html',
  styleUrls: ['./resolved-alerts.component.css']
})
export class ResolvedAlertsComponent implements AfterViewInit, OnDestroy, OnInit {
  @ViewChild(JsonEditorComponent, {static: true}) editor: JsonEditorComponent;
  public editorOptions: JsonEditorOptions;
  alertSource: any;
  virusTotalCount: number;
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
  dtTrigger: Subject<any>[] = [];
  @ViewChildren(DataTableDirective)
  dtElements: QueryList<DataTableDirective>;
  contentEditable = false;
  activeAlerts: any;
  fetched = {};
  aggregated_data:any=[];
  alert_selectedItem:any;
  aggregate_tab_length:any;

  aggregatedOptions: any = {};
  myjson: any = JSON;
  dtTriggerAggregatedAlerts: Subject<any> = new Subject();
  @ViewChild(DataTableDirective, {static: false})
  dtElementt: DataTableDirective;
  aggregatelist:any;
  AggregatedAlertsId:any;
  Comments: any;

  constructor(
    private commonapi: CommonapiService,
    private commonvariable: CommonVariableService,
    private http: HttpClient,
    private titleService: Title,
    private columndefs:Datatablecolumndefs,
  ) {

  }
  toggle: boolean = false;
  ngOnInit() {
    $.fn.dataTable.ext.errMode = 'none';
    debugger
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Resolved alerts");
    this.commonapi.alerts_source_count_api_resolved().subscribe((res: any) => {
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
    this.Get_aggregated_data_filter_with_QueryName(null)
  }

  get_options(source) {
    var that=this;
    return {
      pagingType: 'full_numbers',
      pageLength: 10,
      serverSide: true,
      processing: true,
      searching: true,
      destroy: true,
      "language": {
        "search": "Search: "
      },
      ajax: (dataTablesParameters: any, callback) => {
        var body = dataTablesParameters;
        body['limit'] = body['length'];
        body['source'] = source;
        var searching=false;
        if (body.search.value != "" && body.search.value.length >= 1) {
          body['searchterm'] = body.search.value;
          searching=true;
        }

        if (body['searchterm'] == undefined) {
            body['searchterm'] = "";
        }
        body['resolved'] = true;
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
            this.alertSourceData[source].forEach(element => {
              if(element.verdict == '' || element.verdict == null || element.verdict ==undefined){
                element.verdict = 'N/A'
              }
            });
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
    if(this.dtTrigger[source] == undefined) {
      this.dtTrigger[source] = new Subject<any>();
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
  showResolveComments(data){
    debugger
    if(data == null || data == ''){
      this.Comments = 'No comments added'
    }
    else{
      this.Comments = data
    }
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

  unresolveAlert(AlertId,source) {
    let unresolve_alets_data={}
    unresolve_alets_data["resolve"]=false
    unresolve_alets_data['alert_ids']=AlertId
    swal({
      title: 'Are you sure?',
      text: "Want to unresolve the alert!",
      icon: 'warning',
      buttons: ["Cancel","Yes,UnResolve"],
      dangerMode: true,
      closeOnClickOutside: false,
    }).then((willDelete) => {
      if (willDelete) {
        this.commonapi.AlertsResolve(unresolve_alets_data).subscribe(res => {
          if (res['status'] == "success") {
          swal({
            icon: 'success',
            title: 'UnResolved',
            text: 'Alert has been successfully UnResolved',
            buttons: [false],
            timer: 2000
          })
        }else {
          swal({
            icon: "warning",
            text: res['message'],
            buttons: [true],
          })
        }
          setTimeout(() => {
            this.dtTrigger[source].next();
          }, 1000);
        })
      }
    })
  }

  unresolvedAllSelected(source){
   let unresolve_alets_data={}
   unresolve_alets_data["resolve"]=false
   unresolve_alets_data['alert_ids']=this.checkedList[source]
    if(this.checkedList[source].length==0){
    } else{
      swal({
        title: 'Are you sure?',
              text: "Want to unresolve the alerts!",
              icon: 'warning',
              buttons: ["Cancel", "Yes,UnResolve"],
              dangerMode: true,
              closeOnClickOutside: false,
        }).then((willDelete) => {
        if (willDelete) {
          this.commonapi.AlertsResolve(unresolve_alets_data).subscribe(res => {
            if (res['status'] == "success") {
              swal({
                icon: 'success',
                title: 'UnResolved',
                text: 'Alerts has been successfully UnResolved',
                buttons: [false],
                timer: 2000
              })
            } else {
              swal({
                icon: "warning",
                text: res['message'],
                buttons: [true],
              })
            }
        })
      setTimeout(() => {
        this.dtTrigger[source].next();
      }, 1000);

        }
        })
  }
  }

  toggleDisplay(source) {
    this.fetched[source] = true;
    this.dtTrigger[source].next();
    }
    show_hide_div(name: any) {
      $('.nav-link-active').removeClass("active");
      $('#' + name).addClass("active");
      $('.alert_source_div').hide();
      $('#div_' + name).show();
      $('.no_data').hide();
      if (this.fetched[name] != true) {
        this.toggleDisplay(name);
      }
    }

  // Start Aggregated alerts
  get_alerts_aggregated_data(id){
    this.AggregatedAlertsId=id
    this.aggregated_data=[]
    $('.aggregation_loader').show();
    $('.aggregated_table_data').hide();
    this.commonapi.get_alerts_aggregated_data(id).subscribe((res: any) => {
      $('.aggregation_loader').hide();
      this.aggregate_tab_length=res.data.length
     for(const i in res.data){
       this.aggregated_data.push(res.data[i].query_name)
      }
      if(this.aggregated_data!=0){
        this.Get_aggregated_data_filter_with_QueryName(this.aggregated_data[0]);
      }else{

      }
    })

  }
  Get_aggregated_data_filter_with_QueryName(name){
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
        var payload = {
              "query_name":this.alert_selectedItem,
              "start":body['start'],
              "limit":body['length'],
              "searchterm":searchitem,
        }
        this.http.post<AggregatedDataTablesResponse>(environment.api_url+"/alerts/"+this.AggregatedAlertsId+"/alerted_events", payload, { headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res =>{
          this.aggregatelist = res.data['results'];
          if(this.aggregatelist.length >0 &&  this.aggregatelist!=undefined)
          {
            $('#'+'AggregatedData_table_paginate').show();
            $('#'+'AggregatedData_table_info').show();
          }
          else{
            if(body.search.value=="" || body.search.value == undefined){
              this.errorMessage="No Data Found";
            }
            else{
              this.errorMessage="No Matching Record Found";
            }
            $('#'+'AggregatedData_table_paginate').hide();
            $('#'+'AggregatedData_table_info').hide();
          }
          callback({

            recordsTotal: res.data['count'],
            recordsFiltered: res.data['count'],
            data: []
          });
        });
      },

      ordering: false,
      columns: [{ data: 'line' }]
    }
    // this.dtTriggerr.next();
  }
  action(event): void {
    event.stopPropagation();
  }
   // End Aggregated alerts
}
