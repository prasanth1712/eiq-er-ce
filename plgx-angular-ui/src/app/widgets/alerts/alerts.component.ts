import { AfterViewInit, Component, OnDestroy, OnInit, QueryList, ViewChild, ViewChildren, Input, Injectable } from '@angular/core';
import {Observable} from 'rxjs';
import { DataTablesModule } from 'angular-datatables';
import { DataTableDirective } from 'angular-datatables';
import { Subject } from 'rxjs';
import { HttpClient, HttpResponse } from '@angular/common/http';
import { CommonapiService } from '../../dashboard/_services/commonapi.service';
import { JsonEditorComponent, JsonEditorOptions } from 'ang-jsoneditor';
import { FormBuilder, FormGroup, Validators, FormControl } from '@angular/forms';

import { environment } from '../../../environments/environment';
import { Router, ActivatedRoute } from '@angular/router';
import { DatepickerModule, DatepickerOptions } from 'ng2-datepicker';
import { NgModule } from '@angular/core';
import { Location } from '@angular/common';
import { NgbDateStruct, NgbDate, NgbCalendar, NgbInputDatepickerConfig } from '@ng-bootstrap/ng-bootstrap';
import { flyInOutRTLAnimation } from '../../../assets/animations/right-left-animation';
import { AngularMultiSelect } from 'angular2-multiselect-dropdown';
import { AlertService } from '../../dashboard/_services/alert.service';

declare var links: any;
import swal from 'sweetalert';
import { moment } from "vis-timeline";
import '../../../assets/js/patternfly/patternfly.min.js'
import { th, tr } from 'date-fns/locale';
import { AuthorizationService } from '../../dashboard/_services/Authorization.service';
import { active } from 'd3';
import Swal from 'sweetalert2';
import {saveAs} from 'file-saver';

class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}
export interface CustomResponse {
  data: any;
  message: any;
  status: any;
}
@Injectable({providedIn:'root'})
@Component({
  selector: 'app-alerts',
  templateUrl: './alerts.component.html',
  animations: [flyInOutRTLAnimation],
  styleUrls: ['./alerts.component.css', './alerts.component.scss'],
})


export class AlertsComponent implements AfterViewInit, OnDestroy, OnInit {
  @ViewChild(JsonEditorComponent, { static: true }) editor: JsonEditorComponent;
  selectedDate = {};
  public editorOptions: JsonEditorOptions;
  alertSource: any;
  options = {};
  datepicker_date = {};
  virusTotalCount: number;
  alert_data: any;
  IBMForceTotalCount: number;
  AlientTotalVault: number;
  IOCTotalCount: number;
  RuleTotalCount: number;
  alertSourceData: any;
  alerted_data_json: any;
  alert_nav_data: any = [];
  alerts_graph_data: any;
  alert_title: any;
  errorMessage:any;
  errorMessageAggregated:any;
  all_options = {};
  title = 'Angular 7 CheckBox Select/ Unselect All';
  masterSelected = {};
  checklist: any = [];
  checkedList: any = [];
  checklistAlert: any = [];
  fetched = {};
  events_ids = [];
  @ViewChildren(DataTableDirective)
  dtElements: QueryList<DataTableDirective>;
  dtElement: DataTableDirective;
  activeAlerts: any;
  alertType: any;
  purge_data_duration: any;
  submitted = false;
  verdict: any;
  AlertId: any;
  source: any;
  multipleSelect: boolean = false;
  animationState = 'out';
  resolveAlertForm: FormGroup;
  // public isVisible: boolean;
  public isHostVisible: boolean;
  public isRuleVisible: boolean;
  public isHostFilter: boolean = false;
  public isRuleFilter: boolean = false;
  public isRuleTypeFilter: boolean = false;
  public isRuleFilterBtn: boolean = false;
  // enableChild = false;
  enableHost = false;
  enableRule = false;
  eventID: string;
  eventStatus: string;
  startDate: NgbDate;
  endDate: NgbDate;
  ruleNameList: any = new Array();
  alertData: any;
  public hostData: any = [];
  hostListSelectedItems = [];
  ruleTypeSelectedItems = [];
  ruleNameSelectedItems = [];
  alertStatusSelectedItems = [];
  severityListSelectedItems = [];
  filterListDropdownSettings = {}
  public ngFilterSettings = {};
  response_data: any;
  resHostNames: any;
  res_results: any;
  hostDefault = new FormControl('');
  severityDefault = new FormControl('');
  ruleTypeDefault = new FormControl('');
  ruleNameDefault = new FormControl('');
  alertStatusDefault = new FormControl('');
  public selectedHostsId: any;
  public selectedSeverity: any;
  public selectedRuleType: any;
  public selectedRuleName: any;
  public selectedAlertStatus: any;
  dtTrigger: Subject<any> = new Subject();
  maxDate: any;
  searchText: string = '';
  node_id: any;
  rule_id: any;
  public host_Data: any = [];
  hostdetail:any;
  filter_alerts_with_Hostname:any;
  hostname:any;
  public hostList = [];
  ruleDataName: any;

  alertSelectedItem:any;
  aggregatedData:any={};
  aggregate_tab=[];
  aggregatedOptions: any = {};
  id: any;
  aggregateoutput:any;
  aggregatelist:any;
  dtTriggerAggregatedAlerts: Subject<any> = new Subject();
  myjson: any = JSON;
  aggregateTabLength:any;
  isAlertSelected:boolean = false;
  @ViewChild('dropdownRef',{static:false}) dropdownRef: AngularMultiSelect;
  role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess}
  severityList = [
    { item_id: 'info', item_text: 'Info' },
    { item_id: 'low', item_text: 'Low' },
    { item_id: 'medium', item_text: 'Medium' },
    { item_id: 'high', item_text: 'High' },
    { item_id: 'critical', item_text: 'Critical' },
  ];
  ruleTypeList = [
    { item_id: 'rule', item_text: 'Rule' },
    { item_id: 'ioc', item_text: 'IOC' },
    { item_id: 'alienvault', item_text: 'AlienVault' },
    { item_id: 'ibmxforce', item_text: 'IBM X-Force' },
    { item_id: 'virustotal', item_text: 'VirusTotal' },
  ];
  alertStatusList = [
    { item_id: 'open', item_text: 'New' },
    { item_id: 'true_positive', item_text: 'Resolved - true positive' },
    { item_id: 'false_positive', item_text: 'Resolved - false positive' },
  ];
  constructor(
    private commonapi: CommonapiService,
    private http: HttpClient,
    private _Activatedroute: ActivatedRoute,
    private _location: Location,
    private calendar: NgbCalendar,
    private config: NgbInputDatepickerConfig,
    private formBuilder: FormBuilder,private authorizationService: AuthorizationService,private router: Router,private alertService: AlertService
  ) {
    var today = new Date(); this.maxDate = { year: today.getFullYear(), month: today.getMonth() + 1, day: today.getDate()+ 1 }
    this.isHostVisible = false
    this.isRuleVisible = false
    // this.setDefault();
    this.getHosts();
    this.getRuleNames();
  }

  toggle: boolean = false;
  selectedRow: number;
  selectOpenedList = [];
  openDropdown(){
    this.dropdownRef.openDropdown();
  }
  async toggleShowDiv(alrowData) {
    this.eventID = alrowData.id;
    this.eventStatus = alrowData.status;
    this.alerted_data_json = alrowData.alerted_entry;
    this.isHostVisible = false;
    this.isRuleVisible = false;
  }
  toggleHideDiv() {
    this.selectedRow = null;
  }
  public nodeData: any;
  public ruleData: any;
  public host_data: any;
  public rule_data: any;
  fetchData(nodeID) {
    return this.hostData.filter(x => x.id === nodeID);
  }
  fetchRuleData(ruleID){
    return this.resHostNames.filter(x => x.id === ruleID);
  }
  toggleHostShowDiv(nodeID) {
    setTimeout(() => {
      this.nodeData = this.fetchData(nodeID);
      this.host_data = this.nodeData[0];
      this.enableHost = true;
      this.isHostVisible = true;

      this.isRuleVisible = false;
    }, 300);
  }
  toggleRuleShowDiv(ruleID) {
    this.ruleData = this.fetchRuleData(ruleID);
    this.rule_data = this.ruleData[0];
    // localStorage.setItem('path', 'rule');
    $('.rule_body2').hide();
    $('.rule_body').show();
    console.log(this.rule_data);
    this.isRuleFilterBtn = false
    this.enableRule = true;
    this.isRuleVisible = true;
    this.isHostVisible = false;
  }
  toggleHostHideDiv() {
    this.selectedRow = null;
    this.enableHost = false;
    this.isHostVisible = false;
  }
  toggleRuleHideDiv() {
    this.selectedRow = null;
    this.enableRule = false;
    this.isRuleVisible = false;
  }

  setDefault() {
    this.selectedHostsId = [];
    this.selectedSeverity = [];
    this.selectedRuleType = [];
    this.selectedRuleName = [];
    this.selectedAlertStatus = [];
    this.hostListSelectedItems = [];
    this.severityListSelectedItems = [];
    this.ruleTypeSelectedItems = [];
    this.ruleNameSelectedItems = [];
    this.alertStatusSelectedItems = [];
    this.endDate = this.calendar.getToday();
    this.startDate = this.calendar.getPrev(this.endDate, 'd', 7);
  }
  ngOnInit() {
    $.fn.dataTable.ext.errMode = 'none';

    this.setDefault();
    this.ngFilterSettings ={
      singleSelection: false,
      idField: 'item_id',
      textField: 'item_text',
      enableCheckAll: true,
      selectAllText: 'any',
      unSelectAllText: 'any',
      allowSearchFilter: false,
      limitSelection: -1,
      clearSearchFilter: true,
      maxHeight: 197,
      itemsShowLimit: 1,
      closeDropDownOnSelection: false,
      showSelectedItemsAtTop: false,
      defaultOpen: false,
    }
    this.filterListDropdownSettings = {
      text: "any",
      singleSelection: false,
      selectAllText: 'Select All',
      unSelectAllText: 'UnSelect All',
      badgeShowLimit: 1,
      lazyLoading: false,
      enableSearchFilter: false,
      classes: 'myclass custom-class'
    };
    this._Activatedroute.queryParams.subscribe(params => {
      this.alertType = this._Activatedroute.snapshot.queryParams["alertType"];
      this.activeAlerts = this._Activatedroute.snapshot.queryParams["from"];
      if (this.alertType == 'rule' || this.alertType == 'alienvault' || this.alertType == 'ibmxforce' || this.alertType == 'virustotal' || this.alertType == 'IOC') {
        this.isRuleFilter = false;
        this.isRuleTypeFilter = true;
        this.isRuleFilterBtn = false;

        if(this.alertType == 'alienvault'){
          this.ruleTypeSelectedItems.push({ item_id: 'alienvault', item_text: 'AlienVault' });
          this.ruleTypeDefault = new FormControl(this.ruleTypeSelectedItems);
          this.selectedRuleType = 'alienvault';
        }
        else if(this.alertType == 'ibmxforce'){
          this.ruleTypeSelectedItems.push({ item_id: 'ibmxforce', item_text: 'IBM X-Force' });
          this.ruleTypeDefault = new FormControl(this.ruleTypeSelectedItems);
          this.selectedRuleType = 'ibmxforce';
        }
        else if(this.alertType == 'virustotal'){
          this.ruleTypeSelectedItems.push({ item_id: 'virustotal', item_text: 'VirusTotal' });
          this.ruleTypeDefault = new FormControl(this.ruleTypeSelectedItems);
          this.selectedRuleType = 'virustotal';
        }
        else if(this.alertType == 'IOC'){
          this.ruleTypeSelectedItems.push({ item_id: 'ioc', item_text: 'IOC' });
          this.ruleTypeDefault = new FormControl(this.ruleTypeSelectedItems);
          this.selectedRuleType = 'ioc';
        }
        else {
          this.ruleTypeSelectedItems.push({ item_id: 'rule', item_text: 'Rule' });
          this.ruleTypeDefault = new FormControl(this.ruleTypeSelectedItems);
          this.selectedRuleType = 'rule';
        }

        this.selectedAlertStatus = 'open'
        this.alertStatusSelectedItems.push({ item_id: 'open', item_text: 'New' });
        this.alertStatusDefault = new FormControl(this.alertStatusSelectedItems);
        if(this.activeAlerts == 'host'){
          this.isHostFilter = true;
          this.node_id = this._Activatedroute.snapshot.queryParams["id"];
          this.commonapi.host_name_api(this.node_id).subscribe(res => {
            this.hostdetail = res;
            if (this.hostdetail.status == "failure") {
              this.pagenotfound();
            }
            else {
              this.filter_alerts_with_Hostname = this.hostdetail.data.host_identifier;
              if (this.hostdetail.data.id == this.node_id) {
                this.hostname = this.hostdetail.data.node_info.computer_name;
              }
              this.hostListSelectedItems.push({ item_id: this.filter_alerts_with_Hostname, item_text: this.hostname });
              this.hostDefault = new FormControl(this.hostListSelectedItems)
            }
          });
          this.isRuleTypeFilter = true;
          this.commonapi.host_name_api(this.node_id).subscribe(res => {
            this.filter_alerts_with_Hostname = res['data'].host_identifier
            this.hostname = res['data'].node_info.computer_name
            this.get_alerts_source_count(this.filter_alerts_with_Hostname)
          })
        }
        else{
          this.getAlertData();
          setTimeout(() => {

            this.show_hide_div(this.selectedRuleType);
          }, 300);
        }
      }
      else if (this.activeAlerts == 'er-rule') {
        this.isRuleFilter = true;
        this.isRuleTypeFilter = true;
        this.isRuleFilterBtn = false;
        this.rule_id = this._Activatedroute.snapshot.queryParams["id"]
        this.selectedRuleName = this.rule_id;
        this.selectedRuleType = 'rule';
        this.commonapi.rules_api().subscribe((res: any) => {
          this.resHostNames = res.data.results
          this.resHostNames.forEach(element => {
            if (element.id == this.rule_id) {
              // this.ruleNameList.push({ id: element.id, item_text: element.name });
              this.ruleNameSelectedItems.push({ item_id: this.rule_id, item_text: element.name });
              this.ruleNameDefault = new FormControl(this.ruleNameSelectedItems)
              this.ruleTypeSelectedItems.push({ item_id: 'rule', item_text: 'Rule' });
              this.ruleTypeDefault = new FormControl(this.ruleTypeSelectedItems)
              this.selectedAlertStatus = 'open'
              this.alertStatusSelectedItems.push({ item_id: 'open', item_text: 'New' });
              this.alertStatusDefault = new FormControl(this.alertStatusSelectedItems);
              this.getAlertData();
              setTimeout(() => {

                this.show_hide_div(this.selectedRuleType);
              }, 300);
            }
          });
          // for (const i in this.resHostNames) {
          //   this.ruleNameList.push({ id: this.resHostNames[i].id, item_text: this.resHostNames[i].name });
          // }
          // this.ruleData = this.fetchRuleData(this.rule_id);

        })
        // localStorage.setItem('path','');
      }
      else {
        this.setDefault();
        this.isRuleFilterBtn = true;
        this.isHostFilter = false;
        this.isRuleTypeFilter = false;
        this.isRuleFilter = false;
        // this.setDefault();
        this.ruleTypeDefault = new FormControl();
        this.hostDefault = new FormControl();
        this.alertStatusDefault = new FormControl();
        var selectedDate = this.endDate;
        var selectedStartDate = this.startDate;
        var date = selectedDate.year + '-' + selectedDate.month + '-' + selectedDate.day;
        var selectedstartDate = this.startDate
        var startdate = selectedstartDate.year + '-' + selectedstartDate.month + '-' + selectedstartDate.day;
        this.get_Platform_settings();
        var alerttype = ['rule', 'virustotal', 'ioc', 'alienvault', 'ibmxforce']
        this.getAlertData();
        setTimeout(() => {
          // this.getAlertData();
          this.show_hide_div(this.selectedRuleType);
        }, 300);
      }
    });
    this.resolveAlertForm = this.formBuilder.group({
      comment: '',
      resolveAlert: new FormControl(null, [Validators.required]),
    })
    $('#hidden_button').bind('click', (event, source, event_ids) => {
      this.toggleDisplay(source, event_ids);
    });

    this.GetAggregatedDataFilterWithQueryName(null);
  }

  pagenotfound() {
    this.router.navigate(['/pagenotfound']);
  }
  getHosts() {
    let tmp = [];
    this.commonapi.Hosts_main().subscribe((res: any) => {
      this.response_data = res;
      this.res_results = res.data.results
      for (const i in this.res_results) {
        this.hostData.push(this.res_results[i]);
        tmp.push({ item_id: this.res_results[i].host_identifier, item_text: this.res_results[i].display_name });
      }
      this.hostList = tmp;
    })
  }
  getRuleAlerts(){
    this.router.navigateByUrl('/', {skipLocationChange: true}).then(()=>
        this.router.navigate(['/alerts'],{queryParams: { 'id': this.rule_data.id, 'from':'er-rule' }}));
  }
  get_alerts_source_count(host_identifier){
    var selectedDate = this.endDate;
    var selectedStartDate = this.startDate;
    var date = selectedDate.year + '-' + selectedDate.month + '-' + selectedDate.day;
    var selectedstartDate = this.startDate
    var startdate = selectedstartDate.year + '-' + selectedstartDate.month + '-' + selectedstartDate.day;
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
    this.selectedHostsId = this.filter_alerts_with_Hostname;
    this.getAlertData();
    setTimeout(() => {

      this.show_hide_div(this.selectedRuleType);
    }, 300);
  })
}
  tableSearch() {
    var selectedDate = this.endDate;
    var selectedStartDate = this.startDate;
    var date = selectedDate.year + '-' + selectedDate.month + '-' + selectedDate.day;
    var selectedstartDate = this.startDate
    var startdate = selectedstartDate.year + '-' + selectedstartDate.month + '-' + selectedstartDate.day;
    this.searchText = (<HTMLInputElement>document.getElementById('customsearch')).value;
    this.dtTrigger.next();
  }
  getRuleNames() {
    let tmp = [];
    this.commonapi.rules_api().subscribe((res: any) => {
      this.resHostNames = res?.data?.results;
      for (const i in this.resHostNames) {
        tmp.push({ item_id: this.resHostNames[i].id, item_text: this.resHostNames[i].name });
      }
      this.ruleNameList = tmp;
      console.log(this.ruleNameList);
    })
  }
  validDateFormat(value) {
    if (value) {
      let date = value.substring(0, 10);
      let time = value.substring(11, 19);
      let millisecond = value.substring(20)
      let date1 = date.split('-')[0];
      let date2 = date.split('-')[1];
      let date3 = date.split('-')[2];
      let validDate = date3 + '-' + date2 + '-' + date1 ;
      return validDate
    }

    return null;

  }
  getSelectedValue(isSelected, selectedHost) {

  }
  getStringConcatinated(array_object) {
    //Join Array elements together to make a string of comma separated list
    let string_object = "";
    try {
      if (array_object.length > 0) {
        string_object = array_object[0].item_id;
        for (let index = 1; index < array_object.length; index++) {
          string_object = string_object + ',' + array_object[index].item_id;
        }
        return string_object
      }
      else if(array_object.length == 0){
        return ""
      }
    }
    catch (Error) {
      return ""
    }
  }
  onItemSelectHost(item: any) {
    let hostid = "";
    hostid = this.getStringConcatinated(this.hostListSelectedItems);
    this.selectedHostsId = hostid;
    this.dtTrigger.next();
  }
  OnItemDeSelectHost(item: any) {
    let hostid = "";
    hostid = this.getStringConcatinated(this.hostListSelectedItems);
    this.selectedHostsId = hostid;
    this.dtTrigger.next();
  }
  onSelectAllHost(items: any) {
    this.selectedHostsId = [];
    this.dtTrigger.next();
  }
  onDeSelectAllHost(items: any) {
    this.selectedHostsId = [];
    this.dtTrigger.next();
  }
  onItemSelectSeverity(item: any) {
    this.selectedSeverity = this.getStringConcatinated(this.severityListSelectedItems);
    this.dtTrigger.next();
  }
  OnItemDeSelectSeverity(item: any) {
    this.selectedSeverity = this.getStringConcatinated(this.severityListSelectedItems);
    this.dtTrigger.next();
  }
  onSelectAllSeverity(items: any) {
    this.selectedSeverity = [];
    this.dtTrigger.next();
  }
  onDeSelectAllSeverity(items: any) {
    this.selectedSeverity = [];
    this.dtTrigger.next();
  }
  onItemSelectRuleType(item: any) {
    this.selectedRuleType = this.getStringConcatinated(this.ruleTypeSelectedItems);
    this.dtTrigger.next();
  }
  OnItemDeSelectRuleType(item: any) {
    this.selectedRuleType = this.getStringConcatinated(this.ruleTypeSelectedItems);
    this.dtTrigger.next();
  }
  onSelectAllRuleType(items: any) {
    this.selectedRuleType = [];
    this.dtTrigger.next();
  }
  onDeSelectAllRuleType(items: any) {
    this.selectedRuleType = [];
    this.dtTrigger.next();
  }
  onItemSelectRuleName(item: any) {
    this.selectedRuleName = this.getStringConcatinated(this.ruleNameSelectedItems);
    this.dtTrigger.next();
  }
  OnItemDeSelectRuleName(item: any) {
    this.selectedRuleName = this.getStringConcatinated(this.ruleNameSelectedItems);
    this.dtTrigger.next();
  }
  onSelectAllRuleName(items: any) {
    this.selectedRuleName = [];
    this.dtTrigger.next();
  }
  onDeSelectAllRuleName(items: any) {
    this.selectedRuleName = [];
    this.dtTrigger.next();
  }
  onItemSelectAlertStatus(item: any) {
    this.selectedAlertStatus = this.getStringConcatinated(this.alertStatusSelectedItems);
    this.dtTrigger.next();
  }
  OnItemDeSelectAlertStatus(item: any) {
    this.selectedAlertStatus = this.getStringConcatinated(this.alertStatusSelectedItems);
    this.dtTrigger.next();
  }
  onSelectAllAlertStatus(items: any) {
    this.selectedAlertStatus = [];
    this.dtTrigger.next();
  }
  onDeSelectAllAlertStatus(items: any) {
    this.selectedAlertStatus = [];
    this.dtTrigger.next();
  }
  onResieNavMenu(alertNavData){
    this.alerts_graph_data = alertNavData?.data;
    setTimeout(() => {
    }, 300);
  }
 

  get_options() {
    var that = this;
    return {
      pagingType: 'full_numbers',
      pageLength: 10,
      serverSide: true,
      processing: true,
      searching: false,
      InfoPostFix: false,
      InfoFiltered: false,
      order: [],
      dom: "<'row'<'col-sm-12'f>>" +
      "<'row table-scroll-hidden'<'col-sm-12 mt-18 table-scroll full-height'tr>>" +
      "<'row table-controls custom-pagination-margin'<'col-sm-6 table-controls-li pl-0'li><'col-sm-6 pr-0'p>>",
        "initComplete": function (settings, json) {
          $("#alerts_table").wrap("<div class='table-parent' style='width:100%;position:relative;min-width: 500px;'></div>");
        },
      buttons: [
        {
          text: 'Export',
          action: function (e, dt, node, config) {
            that.exportAlerts();
          }
        }
      ],

      "language": {
        "search": "Search: ",
        "sInfoFiltered": "",
        "lengthMenu": "<ng-container class=custom-pagination-length>Results per page: _MENU_</ng-container>",
        "info" : "Showing _START_ to _END_ of <b>_TOTAL_</b> entries",
      },

      ajax: (dataTablesParameters: any, callback) => {
        var body = dataTablesParameters;
        var selectedDate = this.endDate;
        var selectedStartDate = this.startDate;
        var date = selectedDate.year + '-' + selectedDate.month + '-' + selectedDate.day;
        var selectedstartDate = this.startDate
        var startdate = selectedstartDate.year + '-' + selectedstartDate.month + '-' + selectedstartDate.day;
        body['limit'] = body['length'];
        body['host_identifier'] = this.selectedHostsId;
        body['source'] = this.selectedRuleType;
        body['rule_id'] = this.selectedRuleName;
        body['severity'] = this.selectedSeverity;
        body['verdict'] = this.selectedAlertStatus;
        body['start_date'] = startdate;
        body['end_date'] = date;
        var searching = false;
        if (this.searchText != "" && this.searchText.length >= 1) {
          body['searchterm'] = this.searchText;
          searching = true;
        }
        else if (this.searchText == undefined) {
          body['searchterm'] = "";
        }

        if (this.events_ids.length > 0) {
          body['event_ids'] = this.events_ids;

        }
        if (body.order != "" && body.order.length >= 1) {
          body["column"] = body.columns[body.order[0].column - 1].data
          body["order_by"] = body["order"][0].dir;
        }

        this.removeSelectedAlert();
        this.http.post<DataTablesResponse>(environment.api_url + "/alerts", body, {
          headers: {
            'Content-Type': 'application/json',
            'x-access-token': localStorage.getItem('token')
          }
        }).subscribe(res => {
          this.checklist = [];
          // console.log(res.data['results']);
          if (res.data['count'] > 0 && res.data['results'] != undefined) {
            this.alertSourceData = res.data['results'];
            // console.log(this.alertSourceData);
            this.masterSelected = false;
            for (const i in this.alertSourceData) {
              if(this.alertSourceData[i].source == "rule"){
                this.alertSourceData[i]["Alert"] = this.alertSourceData[i].rule?.name + " " + this.alertSourceData[i].id;
              }
              else{
                this.alertSourceData[i]["Alert"] = this.alertSourceData[i].source + " " + this.alertSourceData[i].id;
              }
              let checkboxdata = {}
              checkboxdata['id'] = this.alertSourceData[i].id;
              checkboxdata['isSelected'] = false
              checkboxdata['status'] = this.alertSourceData[i].status;
              this.checklist.push(checkboxdata);
            }
            // this.getCheckedItemList('');
            if (this.alertSourceData.length > 0 && this.alertSourceData != undefined) {
              this.alertSourceData = res.data['results'];
              this.alertSourceData.sort((x, y) => y.status - x.status)
            }
            // $("#DataTables_Table_0_info").
            $('#alerts_table_paginate').show();
            $('#alerts_table_info').show();

            this.errorMessage = ''
          } else {
            var totalCount
            if (!searching) {
              if (totalCount > 0) {
                this.errorMessage = "No alerts found for the selected duration";
              }
              else {
                this.errorMessage = "No alerts found";
              }


              $('#alerts_table_paginate').hide();
              $('#alerts_table_info').hide();
              $('#alerts_table_length').hide();
            } else {
              this.errorMessage = "No Data";
              $('#alerts_table_paginate').hide();
              $('#alerts_table_info').hide();
              $('#alerts_table_length').hide();
            }
          }
          callback({
            recordsTotal: res.data['total_count'],
            recordsFiltered: res.data['count'],
            data: []
          });
        },
        error => {
          swal({
            icon: 'error',
            title: 'failure',
            text: error?.error?.message?.message,
            }).then((isError) => {
              if (isError) {
                setTimeout(() => {
                  this.setDefault();
                  this.dtTrigger.next();
                },200);
            }
          })
        });
      },
      columns: [{ data: 'alert' }, { data: 'status' }, { data: 'hostname' }, { data: 'severity' }, { data: 'created_at' }, {data: 'name'}, {data: 'aggregated_events_count'}],
      columnDefs: [{
        targets: [0, 1,6,8], /* column index */
        orderable: false
      }],
    }
  }
  showdataResolved(any, title) {
    this.alert_title = title;

    this.toggle = false;
    setTimeout(() => {
      this.editorOptions = new JsonEditorOptions();
      this.editorOptions.mode = 'view';
      this.alerted_data_json = any;
      this.toggle = true;
    }, 100);
  }
  unresolveAlert(AlertId, source) {
    let unresolve_alets_data = {}
    unresolve_alets_data["resolve"] = false
    unresolve_alets_data['alert_ids'] = AlertId
    swal({
      title: 'Are you sure?',
      text: "Want to unresolve the alert!",
      icon: 'warning',
      buttons: ["Cancel", "Yes,UnResolve"],
      dangerMode: true,
      closeOnClickOutside: false,
    } as any).then((willDelete) => {
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
          } else {
            swal({
              icon: "warning",
              text: res['message'],
              buttons: [true],
            })
          }
          setTimeout(() => {
            this.dtTrigger.next();
          }, 1000);
        })
      }
    })
  }
  getAlertData() {
    var today = new Date();
    this.all_options = this.get_options();
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
  checkUncheckAll() {
    for (var i = 0; i < this.checklist.length; i++) {
      if(this.checklist[i].status === 'OPEN'){
        this.checklist[i].isSelected = this.masterSelected;
      }
      else{
        this.checklist[i].isSelected = false;
      }
      if (this.checklist[i].isSelected == true) {
        this.filterArr = this.checkedList.filter(h => h == this.checklist[i].id)
        if (this.filterArr.length == 0) {
          this.checkedList.push(this.checklist[i].id);
        }
      }
      else {
        this.checkedList = this.checkedList.filter(item => item !== this.checklist[i].id);
      }
    }
    this.selectedCount = this.checkedList.length;
  }


  isAllSelected(id) {
    this.selectHost(id);
    this.masterSelected = this.checklist.every(function (item: any) {
      return item.isSelected == true;
    })
    // this.getCheckedItemList(source);
  }

  getCheckedItemList() {
    this.checkedList = [];
    for (var i = 0; i < this.checklist.length; i++) {
      this.checklist[i].isSelected = this.masterSelected;
      if (this.checklist[i].isSelected == true) {
        this.filterArr = this.checkedList.filter(h => h == this.checklist[i].id);
        if (this.filterArr.length == 0) {
          this.checkedList.push(this.checklist[i].id);
        }
      }
      else {
        this.checkedList = this.checkedList.filter(item => item !== this.checklist[i].id);
      }
    }
    this.selectedCount = this.checkedList.length;
  }

  resolveAlert(alertId, selectOption) {
    this.AlertId = alertId;
    this.multipleSelect = selectOption;
    this.openResolveAlert();
  }
  multiResolveAlert(selectOption) {
    this.multipleSelect = selectOption
    this.openResolveAlert();
  }
  openResolveAlert() {
    let modal = document.getElementById("resolveAlertModal");
    modal.style.display = "block";
  }
  onItemChange(value) {
    this.verdict = value;
  }
  resolveAlertSubmitForm() {
    this.submitted = true;
    if (!this.resolveAlertForm.valid) {
      console.log('Please provide all the required values!');
      $('#resolveAlertModal').show()
      return false;
    } else {
      let resolveAlertsData = {}
      resolveAlertsData["resolve"] = true;

      if (this.multipleSelect == false) { resolveAlertsData['alert_ids'] = this.AlertId; }
      else { resolveAlertsData['alert_ids'] = this.checkedList; }

      if (this.verdict == 'True Positive') {
        resolveAlertsData['verdict'] = true;
      }
      else if (this.verdict == 'False Positive') {
        resolveAlertsData['verdict'] = false;
      }
      resolveAlertsData['comment'] = this.f.comment.value;
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
          this.dtTrigger.next();
          this.closeResolveAlert();
        }, 1000);
      })
    }

  }
  closeResolveAlert() {
    this.submitted = false;
    this.resolveAlertForm.reset()
    let modal = document.getElementById("resolveAlertModal");
    modal.style.display = "none";
  }
  closeModal(modalId) {
    let modal = document.getElementById(modalId);
    modal.style.display = "none";
    $('.modal-backdrop').remove();
  }
  get f() { return this.resolveAlertForm.controls; }
  resolvedAllSelected(source) {
    let resolve_alerts_data = {}
    var selectedDate = this.endDate;
    var selectedStartDate = this.startDate;
    var date = selectedDate.year + '-' + selectedDate.month + '-' + selectedDate.day;
    var selectedstartDate = this.startDate
    var startdate = selectedstartDate.year + '-' + selectedstartDate.month + '-' + selectedstartDate.day;
    resolve_alerts_data["resolve"] = true
    resolve_alerts_data['alert_ids'] = this.checkedList
    if (this.checkedList.length == 0) {
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
            this.dtTrigger.next();
            this.closeResolveAlert();
          }, 3000);
        }
      })
    }
  }

  toggleDisplay(source, events) {
    this.events_ids = events;
    this.dtTrigger.next();
  }

  show_hide_div(name: any) {
    // this.dtTrigger.next();
    this.events_ids = [];
    $('.nav-link-active').removeClass("active");
    $('.alert_source_div').hide();
    $('#div_alerts').show();
    $('.no_data').hide();

    if (this.fetched[name] != true) {
      var selectedDate = this.endDate;
    var selectedStartDate = this.startDate;
    var date = selectedDate.year + '-' + selectedDate.month + '-' + selectedDate.day;
    var selectedstartDate = this.startDate
    var startdate = selectedstartDate.year + '-' + selectedstartDate.month + '-' + selectedstartDate.day;
      this.toggleDisplay(name, []);
    }
    this.alert_data = { "source": name };
  }

  validateDate(dateString) {
    var regEx = /^\d{4}-\d{1,2}-\d{1,2}$/;
    if (!dateString.match(regEx)) return false;  // Invalid format
    var d = new Date(dateString.replace(/-/g, "/"));
    var dNum = d.getTime();
    if (!dNum && dNum !== 0) return false; // NaN value, Invalid date
    return dateString;
  }
  resetDate(){
    this.endDate = this.calendar.getToday();
    this.startDate = this.calendar.getPrev(this.endDate, 'd', 7);
  }
  myHandler(selectedDate) {
    this.events_ids = [];
    if(selectedDate === null || selectedDate === '' || selectedDate === undefined)
    {
      Swal.fire({
        icon: "warning",
        text: "Please provide correct date input",
      }).then((result) => {
        if (result.value) {
          setTimeout(() => {
            this.resetDate();
            this.dtTrigger.next();
          },200);
        }
     })
      return;
    }
    else{
      var date = selectedDate.year + '-' + selectedDate.month + '-' + selectedDate.day;
      var temp = this.validateDate(date)
        if(temp){
          setTimeout(() => {
            this.grabNewDataBasedOnDate();
            this.dtTrigger.next();
          }, 400);
        }
        else{
          Swal.fire({
            icon: "warning",
            text: "Please provide correct date input",
          }).then((result) => {
            if (result.value) {
              setTimeout(() => {
                this.resetDate();
                this.dtTrigger.next();
              },200);
            }
         })
          return;
        }
    }
  }

  grabNewDataBasedOnDate() {
    var selectedDate = this.endDate;
    var selectedStartDate = this.startDate;
    var date = selectedDate.year + '-' + selectedDate.month + '-' + selectedDate.day;
    var selectedstartDate = this.startDate
    var startdate = selectedstartDate.year + '-' + selectedstartDate.month + '-' + selectedstartDate.day;
    this.getAlertData();
  }

  convert(str) {
    var date = new Date(str),
      mnth = ("0" + (date.getMonth() + 1)).slice(-2),
      day = ("0" + date.getDate()).slice(-2);
    return [date.getFullYear(), mnth, day].join("-");
  }

  convertDate(date) {
    var mnth = ("0" + (date.getMonth() + 1)).slice(-2),
      day = ("0" + date.getDate()).slice(-2);
    return [date.getFullYear(), mnth, day].join("-");
  }

  download() {
    this.exportAlerts();
  }

  /*  Export csv file for all the alert type*/
  exportAlerts() {
    var selectedDate = this.endDate;
    var selectedStartDate = this.startDate;
    var date = selectedDate.year + '-' + selectedDate.month + '-' + selectedDate.day;
    var selectedstartDate = this.startDate
    var startdate = selectedstartDate.year + '-' + selectedstartDate.month + '-' + selectedstartDate.day;
    // var payloadDict = {"source": source, "duration": $('#duration_' + source).val(), "type": $('#type_' + source).val(), "date":this.convertDate(this.datepicker_date[source])}
    var payloadDict = { "source": this.selectedRuleType, "host_identifier": this.selectedHostsId, "rule_id": this.selectedRuleName, "severity": this.selectedSeverity, "verdict": this.selectedAlertStatus, "start_date": startdate, "end_date": date,  }
    console.log(payloadDict);
    if (this.events_ids.length > 0) {
      payloadDict['event_ids'] = this.events_ids;
    }
    var alert_name = JSON.stringify(payloadDict);
    var token_val = localStorage.getItem('token');
    var today = new Date();
    var currentDate = today.getDate() + "-" + (today.getMonth() + 1) + "-" + today.getFullYear();
    $.ajax({
      "url": environment.api_url + "/alerts/alert_source/export",
      "type": 'POST',
      "data": alert_name,
      headers: {
        "content-type": "application/json",
        "x-access-token": token_val
      },
      "success": function (res, status, xhr) {
        if (res.status == 'failure') {
          var csvData = new Blob([res.message], {
            type: 'text/csv;charset=utf-8;'
          });
          var csvURL = window.URL.createObjectURL(csvData);
          var tempLink = document.createElement('a');
          tempLink.href = csvURL;
          tempLink.setAttribute('download', 'alert' + '_' + payloadDict.source + '_' + currentDate + '.csv');
          tempLink.click();
        }
        else {
          var csvData = new Blob([res], {
            type: 'text/csv;charset=utf-8;'
          });
          var csvURL = window.URL.createObjectURL(csvData);
          var tempLink = document.createElement('a');
          tempLink.href = csvURL;
          tempLink.setAttribute('download', 'alert' + '_' + payloadDict.source + '_' + currentDate + '.csv');
          tempLink.click();
        }
      }

    });
    return false;
  }

  get_Platform_settings() {
    this.commonapi.getConfigurationSettings().subscribe(res => {
      this.purge_data_duration = res.data.purge_data_duration;
    });
  }
  Get_total_alerts_based_on_alert_type(name) {
    $(".timeline-event-dot").removeClass("selected")
    this.events_ids = [];
    this.dtTrigger.next();
  }

  goBack() {
    this._location.back();
  }
  selectList = [];
  filterArr: any;
  selectedCount: any = 0;
  selectHost(id) {
    this.filterArr = this.checkedList.filter(h => h == id);
    if (this.filterArr.length == 0) {
      this.checkedList.push(id);
    } else {
      this.checkedList = this.checkedList.filter(item => item !== id);
    }
    this.selectedCount = this.checkedList.length;
  }
  removeSelectedAlert() {
    this.checkedList = [];
    this.selectedRow = null;
    this.selectedCount = this.checkedList.length;
    this.masterSelected = false;
    for (var i = 0; i < this.checklist.length; i++) {
      this.checklist[i].isSelected = false;
    }
  }

  // Start Aggregated alerts
  getAlertsAggregatedData(id){
    this.id = id;
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
      dom: "<'row'<'col-sm-12'f>>" +
      "<'row'<'col-sm-12 mt-18'tr>>" +
      "<'row table-controls'<'col-sm-6 table-controls-li'li><'col-sm-6'p>>",
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
        "search": "Search: ",
        "lengthMenu": "<ng-container class=custom-pagination-length>Results per page: _MENU_</ng-container>",
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
              this.errorMessageAggregated="No Data Found";
            }
            else{
              this.errorMessageAggregated="No Matching Record Found";
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
    var alertId = this.id;
    var today = new Date();
    var currentDate = today.getDate()+"-"+(today.getMonth()+1)+"-"+today.getFullYear();
    this.commonapi.alertedEventsExport(alertId,queryName).subscribe((res: any) => {
      saveAs(res,  'alert'+'_'+this.alertSelectedItem+ '_' + currentDate + '.csv');
    })
  }
  action(event): void {
    event.stopPropagation();
  }

}
