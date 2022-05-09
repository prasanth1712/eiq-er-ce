import {AfterViewInit, Component, OnDestroy, OnInit, QueryList, ViewChild, ViewChildren} from '@angular/core';
import {DataTablesModule} from 'angular-datatables';
import {DataTableDirective} from 'angular-datatables';
import {Subject} from 'rxjs';
import {HttpClient, HttpResponse} from '@angular/common/http';
import {CommonapiService} from '../../../dashboard/_services/commonapi.service';
import {JsonEditorComponent, JsonEditorOptions} from 'ang-jsoneditor';

import {environment} from '../../../../environments/environment';
import {Router, ActivatedRoute} from '@angular/router';
import '../../../../assets/vendors/timeline/lib/timeline.js';
import '../../../../assets/vendors/timeline/lib/timeline-locales.js';
import {NgDatepickerModule, DatepickerOptions} from 'ng2-datepicker';
import {NgModule} from '@angular/core';
import { Location } from '@angular/common';
import { saveAs } from 'file-saver';
declare var links: any;
import swal from 'sweetalert';
import {moment} from "vis-timeline";


class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}


@Component({
  selector: 'app-filter-alerts-with-hostname',
  templateUrl: './filter-alerts-with-hostname.component.html',
  styleUrls: ['./filter-alerts-with-hostname.component.css']
})
@NgModule({
  imports: [
    NgDatepickerModule
  ],

})
export class FilterAlertsWithHostnameComponent implements AfterViewInit, OnDestroy, OnInit {
  @ViewChild(JsonEditorComponent, {static: true}) editor: JsonEditorComponent;
  public editorOptions: JsonEditorOptions;
  id:any;
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
  filter_alerts_with_Hostname:any;
  hostname:any;
  hostdetail:any;
  purge_data_duration:any;
  alertSelectedItem:any;
  aggregatedData:any={};
  aggregate_tab=[];
  aggregatedOptions: any = {};
  aggregateId: any;
  aggregateoutput:any;
  aggregatelist:any;
  dtTriggerAggregatedAlerts: Subject<any> = new Subject();
  myjson: any = JSON;
  aggregateTabLength:any;
  constructor(
    private commonapi: CommonapiService,
    private http: HttpClient,
    private _Activatedroute: ActivatedRoute,
    private router: Router,
    private _location: Location,
  ) {

  }

  toggle: boolean = false;


  ngOnInit() {
    this.get_Platform_settings();
    this._Activatedroute.paramMap.subscribe(params => {
        this.id = params.get('id');
        this.commonapi.host_name_api(this.id).subscribe(res => {
           this.hostdetail = res;
           if(this.hostdetail.status == "failure"){
             this.pagenotfound();
           }
           else{
           this.filter_alerts_with_Hostname = this.hostdetail.data.host_identifier;
           if (this.hostdetail.data.id == this.id) {
             this.hostname = this.hostdetail.data.node_info.computer_name;
           }
         }
         });
      })

      this._Activatedroute.params.subscribe(params => {
        this.activeAlerts = this._Activatedroute.snapshot.queryParams["id"];
        // this.filter_alerts_with_Hostname=localStorage.getItem('hostidentifier')
        // this.hostname=localStorage.getItem('Hostname')
        window.history.replaceState("object or string", "Title",window.location.href.substring(window.location.href.indexOf('/hosts/')).split("?")[0]);
      });

    $('#hidden_button').bind('click', (event, source, event_ids) => {
      this.toggleDisplay(source, event_ids);
    });
    this._Activatedroute.paramMap.subscribe(params => {
      this.id=params.get('id')
    })
    this.commonapi.host_name_api(this.id).subscribe(res => {
      this.filter_alerts_with_Hostname=res['data'].host_identifier
      this.hostname=res['data'].node_info.computer_name
      this.get_alerts_source_count(this.filter_alerts_with_Hostname)
    })
    this.GetAggregatedDataFilterWithQueryName(null);
  }
  get_alerts_source_count(host_identifier){
  this.commonapi.alerts_source_count_api_Host_identifier(host_identifier).subscribe((res: any) => {
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
      // this.getTimelineData(active_souce,undefined,undefined);
    }, 300);
  })
}
  pagenotfound() {
    this.router.navigate(['/pagenotfound']);
  }

  // getTimelineData(source_, duration, type) {
  //   const monthNames = ["January", "February", "March", "April", "May", "June",
  //     "July", "August", "September", "October", "November", "December"
  //   ];
  //   var duration_text="1 week";
  //   if(duration==2){
  //      duration_text="1 day";
  //   } else if (duration==4){
  //      duration_text="1 month";
  //   }
  //   var source = source_;
  //   this.fetched[source] = true;
  //   if (duration == undefined) {
  //     duration = 3;
  //   }
  //   if (type == undefined) {
  //     type = 2;
  //   }
  //   var date =  this.datepicker_date[source];
  //   let date_str;
  //   if(date instanceof Date){
  //     date_str=monthNames[date.getMonth()]+" "+date.getDate()+", "+date.getFullYear();
  //     date=this.convertDate(date);
  //   }else{
  //     var date_array=date.split("-");
  //     date_str=monthNames[date_array[1]-1]+" "+date_array[2]+", "+date_array[0];
  //   }
  //   $('#time_message_'+source).html("Showing data of last "+duration_text+" from "+date_str);
  //   if (date == undefined) {
  //     date = '';
  //   }
  //   this.commonapi.alerts_graph_api_filter_with_Host_identifier(source, duration, type, date,this.filter_alerts_with_Hostname).subscribe((res: any) => {
  //     var end_date=new Date();
  //     end_date.setHours(0,0,0,0);
  //     end_date.setDate(end_date.getDate()+1);
  //
  //
  //     if (date!=undefined&&date!=''){
  //       var date_array=date.split("-");
  //       end_date=new Date(date_array[0], date_array[1]-1, date_array[2]);
  //       end_date.setDate(end_date.getDate()+1);
  //     }
  //     var start_date=new Date(end_date.getFullYear(),end_date.getMonth(),end_date.getDate());
  //
  //
  //     if(duration==2){
  //       start_date.setDate(end_date.getDate()-1);
  //     }
  //     else if(duration==3){
  //       start_date.setDate(end_date.getDate()-7);
  //     }
  //     else if(duration==4){
  //       start_date.setDate(end_date.getDate()-30);
  //     }
  //     var dataNew = [];
  //     if(res.data != null){
  //       res.data.forEach(function (value) {
  //           var start = new Date(value.start);
  //           start.setMinutes(start.getMinutes() + start.getTimezoneOffset())
  //           dataNew.push({
  //            "start" : start.valueOf(),
  //            "content" :value.content,
  //            "event_id": value.event_id,
  //            "className": value.className,
  //         })
  //        });
  //      }
  //     var data = dataNew;
  //     // var data = res.data;
  //     var options = {
  //       'width': '100%',
  //       'height': '125px',
  //       'start': start_date,
  //       'end': end_date,
  //       'cluster': true,
  //       'locale': 'en',
  //       'clusterMaxItems': 1,
  //       'showNavigation': false,
  //     };
  //
  //     // Instantiate our timeline object.
  //     var timeline = new links.Timeline(document.getElementById(source + '_timeline'), options);
  //     // Draw our timeline with the created data and options
  //     if (res.data !== '') {
  //       $('.alert_body_val').show();
  //       $('.alert_body_val2').hide();
  //     }
  //     timeline.draw(data);
  //     $(".timeline-event-dot-"+source + '_timeline').removeClass("selected");
  //
  //     var zoomInValue = 0.4;
  //     var moveValue = 0.2;
  //
  //     function zoom(zoomVal, source) {
  //       timeline.zoom(zoomVal, undefined, source);
  //       timeline.trigger("rangechange");
  //       timeline.trigger("rangechanged");
  //     }
  //
  //     function move(moveVal, source) {
  //       timeline.move(moveVal, source);
  //       timeline.trigger("rangechange");
  //       timeline.trigger("rangechanged");
  //     }
  //
  //     $("#btn-zoom-in" + "_" + source).click(function (e) {
  //       zoom(zoomInValue, source);
  //     });
  //
  //     $("#btn-zoom-out" + "_" + source).click(function (e) {
  //       zoom(-1 * zoomInValue, source);
  //     });
  //
  //     $("#btn-move-left" + "_" + source).click(function (e) {
  //       move(-1 * moveValue, source);
  //     });
  //
  //     $("#btn-move-right" + "_" + source).click(function (e) {
  //       move(moveValue, source);
  //     });
  //     setTimeout(() => {
  //       // move(-1 * moveValue, source);
  //     }, 300);
  //   });
  // }

  get_options(source) {
    var that=this;

    return {
      pagingType: 'full_numbers',
      pageLength: 10,
      serverSide: true,
      processing: true,
      searching: true,

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
      //  },
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


        var date = this.datepicker_date[source];
        if(date instanceof Date){
          date=this.convertDate(date);
        }
        body['type']=type;
        body['duration']=duration;
        body['host_identifier']= this.filter_alerts_with_Hostname;

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

    // var date = today.getFullYear() + '-' + (today.getMonth() + 1) + '-' + today.getDate();
    if(this.dtTrigger[source] == undefined) {
      this.dtTrigger[source] = new Subject<any>();
      this.datepicker_date[source]=today;
      this.options[source] = {
        minYear: 1970,
        maxYear: 2030,
        displayFormat: 'MMM D[,] YYYY',
        barTitleFormat: 'MMMM YYYY',
        dayNamesFormat: 'dd',
        firstCalendarDay: 0, // 0 - Sunday, 1 - Monday
        maxDate: today,  // Maximal selectable date
        barTitleIfEmpty: 'Click to select a date',
        placeholder: 'Click to select a date', // HTML input placeholder attribute (default: '')
        addClass: 'form-control', // Optional, value to pass on to [ngClass] on the input field
        addStyle: {}, // Optional, value to pass to [ngStyle] on the input field
        fieldId: 'datepicker_' + source, // ID to assign to the input field. Defaults to datepicker-<counter>
        useEmptyBarTitle: false, // Defaults to true. If set to false then barTitleIfEmpty will be disregarded and a date will always be shown
      };

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

  resolveAlert(AlertId, source) {
    let resolve_alerts_data={}
    resolve_alerts_data["resolve"]=true
    resolve_alerts_data['alert_ids']=AlertId
    swal({
      title: 'Are you sure?',
      text: "Want to resolve the alert!",
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
            this.dtTrigger[source].next();
            // this.getTimelineData(source,undefined,undefined);
          }, 2000);
        })

      }
    })
  }

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
            // this.getTimelineData(source,undefined,undefined);
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
    this.events_ids=[]
    $('.nav-link-active').removeClass("active");
    $('#' + name).addClass("active");
    $('.alert_source_div').hide();
    $('#div_' + name).show();
    $('.no_data').hide();

    if (this.fetched[name] != true) {
      // this.getTimelineData(name,undefined,undefined);
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
      // this.getTimelineData(source, duration, type);
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
    var payloadDict = {"source": source, "duration": $('#duration_' + source).val(), "type": $('#type_' + source).val(), "date":this.convertDate(this.datepicker_date[source]), "host_identifier": this.filter_alerts_with_Hostname}
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
            tempLink.setAttribute('download', 'alert'+'_'+payloadDict.source+'_'+localStorage.getItem('Hostname')+ '_' + currentDate + '.csv');
            tempLink.click();
          }
          else{
            var csvData = new Blob([res], {
                type: 'text/csv;charset=utf-8;'
            });
            var csvURL = window.URL.createObjectURL(csvData);
            var tempLink = document.createElement('a');
            tempLink.href = csvURL;
            tempLink.setAttribute('download', 'alert'+'_'+payloadDict.source+'_'+localStorage.getItem('Hostname')+ '_' + currentDate + '.csv');
            tempLink.click();
        }
          }

    });
    return false;
}

get_Platform_settings(){
  this.commonapi.getConfigurationSettings().subscribe(res => {
    this.purge_data_duration=res.data.purge_data_duration;
  });
}
goBack(){
  this._location.back();
}
Get_total_alerts_based_on_alert_type(name){
  $(".timeline-event-dot").removeClass("selected")
  this.events_ids=[];
  this.dtTrigger[name].next();
}
// Start Aggregated alerts
getAlertsAggregatedData(id){
  this.aggregateId = id;
  this.aggregatedData = [];
  $('.aggregated_table_data').hide();
  this.commonapi.get_alerts_aggregated_data(id).subscribe((res: any) => {
    $('.aggregation_loader').hide();
    this.aggregateTabLength=res.data.length
   for(const i in res.data){
     this.aggregatedData.push(res.data[i].query_name)
    }
    if(this.aggregatedData!=0){
      this.GetAggregatedDataFilterWithQueryName(this.aggregatedData[0]);
    }else{

    }
  })
}

GetAggregatedDataFilterWithQueryName(name){
  this.dtTriggerAggregatedAlerts.next();
  $('.aggregated_table_data').show();
  var that=this;
  this.alertSelectedItem = name;
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
	          "query_name":this.alertSelectedItem,
	          "start":body['start'],
            "limit":body['length'],
            "searchterm":searchitem,
      }
      this.http.post<DataTablesResponse>(environment.api_url+"/alerts/"+this.aggregateId+"/alerted_events", payload, { headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res =>{
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
  var queryName = this.alertSelectedItem;
  var alertId = this.aggregateId;
  var today = new Date();
  var currentDate = today.getDate()+"-"+(today.getMonth()+1)+"-"+today.getFullYear();
  this.commonapi.alertedEventsExport(alertId,queryName).subscribe((res: any) => {
    saveAs(res,  'alert'+'_'+this.alertSelectedItem+ '_' + currentDate + '.csv');
  })
}
}
