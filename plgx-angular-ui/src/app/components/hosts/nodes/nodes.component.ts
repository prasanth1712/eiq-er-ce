import { AfterViewInit, Component, OnDestroy, OnInit, ViewChild,ElementRef, Input, OnChanges, HostListener } from '@angular/core';
import { Router, ActivatedRoute, NavigationEnd, RoutesRecognized } from '@angular/router';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../../dashboard/_services/commonvariable.service';
import { ActivityComponent } from '../../../components/hosts/activity/activity.component';
import { environment } from '../../../../environments/environment';
// import * as $ from 'jquery';
import { JsonEditorComponent, JsonEditorOptions } from 'ang-jsoneditor';
import { msg } from '../../../dashboard/_helpers/common.msg';
import { Location } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import 'datatables.net';
import { Subject, Subscription } from 'rxjs';
import swal from 'sweetalert';
import { Title } from '@angular/platform-browser';
import { Chart } from 'chart.js';
import 'chartjs-plugin-labels';
import { ToastrService } from 'ngx-toastr';
import { DataTableDirective } from 'angular-datatables';
import { FormGroup, FormBuilder, Validators, FormControl } from '@angular/forms';
import Swal from 'sweetalert2';
import { AuthorizationService } from '../../../dashboard/_services/Authorization.service';
import { compare } from 'compare-versions';
import { moment } from 'vis-timeline';
import { saveAs } from 'file-saver';
import { filter, pairwise } from 'rxjs/operators';
import 'ace-builds/src-noconflict/mode-javascript';
import "ace-builds/webpack-resolver";
import { TagsValidationHandler } from '../../../dashboard/_helpers/tagsValidationHandler';
declare let d3: any;
declare var alerted_entry: any;
let currentQueryID;
let gotResultsFromSocket;
var PaginationIndex
var TempIndex
var DefenderPaginationIndex
var DefenderTempIndex
var DefenderPaginationLength
var DefenderTempLength = DefenderPaginationLength = 10;
var ActivityTempIndex
var ActivityPaginationLength
var ActivityTempLength = ActivityPaginationLength = 10;
var NextDataId;
var SelectedNodeID;
declare var $: any;
class log_data {
  line: string;
  message: string;
  severity: string;
  filename: string;
}

class Defender_log_data {
  columns: string;
}

class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}

class Person {
  id: number;
  firstName: string;
  lastName: string;
}
var set_time_out;
var is_manually_closed_websocket_session:boolean=false
var str = window.location.href;
str = str.substr(str.indexOf(':') + 3);
var socket_ip = str.substring(0, str.indexOf('/'));
//for live terminal
let ws;
var live_url = environment.liveTerminal_response_socket_url;
if (live_url) {
  var socket_url = environment.liveTerminal_response_socket_url;
} else {
  var socket_url = 'wss://' + socket_ip + '/esp-ui/websocket/action/result';
}
//for quarrantine file validation
let wsq;
var live_socket_url = environment.socket_url;
if (live_socket_url) {
  var socket_live_url = environment.socket_url;
} else {
  var socket_live_url = 'wss://' + socket_ip + '/esp-ui/distributed/result';
}
//for stauslog export
let Wssl;
var Statuslog_Socketurl = environment.Statuslog_Export_Socketurl;
if (Statuslog_Socketurl) {
  var Statuslog_Live_Url = environment.Statuslog_Export_Socketurl;
} else {
  var Statuslog_Live_Url = 'wss://' + socket_ip + '/esp-ui/websocket/csv/export';
}
var status
var Timer_count = 0;
var timer_is_on = 0;

export interface CustomResponse {
  data: any;
  message: any;
  status: any;
}
@Component({
  providers:[ActivityComponent],
  selector: 'app-nodes',
  templateUrl: './nodes.component.html',
  styleUrls: ['./nodes.component.scss']
})

export class NodesComponent implements AfterViewInit, OnInit, OnDestroy,OnChanges {
  @ViewChild(JsonEditorComponent, { static: true }) editor: JsonEditorComponent;
  public editorOptions: JsonEditorOptions;
  text:string = "";
  live_test_code='';
  options:any = {maxLines: 1000, printMargin: false};
  id: any;
  sub: any;
  product: any;
  nodes: any;
  node_id: any;
  network_info: any;
  hostDetails: any = {'osquery_version':'', 'extension_version':''};
  node_info: any;
  data: any;
  lastcheckin: any;
  currentdate: any;
  lastcheckindate: any;
  enrolled: any;
  enrolleddate: any;
  laststatus: any;
  laststatusdate: any;
  byte_value: number;
  physical_memory:any;
  lastresult: any;
  lastresultdate: any;
  lastconfig: any;
  lastconfigdate: any;
  lastqueryread: any;
  lastqueryreaddate: any;
  lastquerywrite: any;
  lastquerywritedate: any;
  networkheadeer: any;
  additionaldata: any;
  packs_count: any;
  pack_name: any;
  query_name: any;
  query_names: any;
  pack_query_name: any;
  query_name_value: any;
  query_count: any;
  querydata: any = [];
  pack_data:any = [];
  tags:any[];
  searchText:any;
  action_status:any;
  endpoint:any;
  responseenabled:any;
  queryid:any;
  term:any;
  termQueries:any;
  log_status:any;
  log_data:any;
  errorMessage:any;
  errorMessageLogs:any;
  interval :any;
  dataRefresher: any;
  responce_action:Subscription;
  alerted_data_json:any;
  additional_config_data:any;
  status_log_checkbox=false;
  selectedItem:any;
  ActivityselectedItem:any;
  actionselect:any=0;
  host_identifier:any;
  os_platform:any;
  os_name:any;
  alertlist:any;
  alienvault = <any>{};
  ibmxforce = <any>{};
  rule = <any>{};
  ioc = <any>{};
  virustotal = <any>{};
  selectdays_shows: any;
  customurl : any = "";
  Filepath : any = "";
  FileExtensions : any = "";
  ProcessName : any = "";
  Quicktimepicker:any;
  fulltimepicker:any;
  fullschedulescan:number = 0;
  checkedIDs:any;
  exclusiondata:any;
  scannowdata:any;
  schedulescandata:any;
  currentsettingdata:any;
  viewcurrentdata:any;
  remove_exclusiondata:any;
  viewcurrentarray:any=[];
  Isloading:boolean=false;
  checkupdatedata:any;
  computerstatusdata:any;
  windows_defender_status:any;
  windows_defender_list = [];
  viewopenc2data :any;
  viewopenc2result:any;
  setting_openc2_id:any;
  check_openc2_id:any;
  scan_openc2_id:any;
  schedule_openc2_id:any;
  exclude_openc2_id:any;
  pendingcount = 0;
  settingstatus = 0 ;
  quarantinedata:any;
  quarantine_openc2_id:any;
  remove_exclude_openc2_id:any;
  status_openc2_id:any;
  scantype:any = 1;
  schduletype:any = 1;
  Isscanshow = false;
  Isquicksheduleshow = true;
  Isfullsheduleshow = false;
  Isfulltimeshow = true;
  keys:any;
  defenderstatus = true;
  modaltitle:any;
  successdata:any;
  loadermsg:any;
  defenderTimeout:any;
  defenderlogoutput:any;
  defenderloglist:any;
  myjson: any = JSON;
  Progress_value:number = 0;
  liveterminal_response='';
  cancel_live_terminal_request=false
  Loader_msg_based_on_time:any;
  spinner:boolean=false;
  msg_executing_or_executed:any;
  project_name=this.commonvariable.APP_NAME;
  maxTagCharacters = (environment?.max_tag_size)? environment.max_tag_size : 64;
  osInfo:any;
  startedAt: any;
  hostState: any;
  isSecurityCenterActive: boolean = false;
  newPlatform: any;


  configSelectControl = new FormControl('Any')

  //Recent activity
  nodesdata: any;
  activitynode: any;
  selected_query:any;
  activitydata: any;
  activitycount: any;
  defaultData: boolean;
  queryname: any;
  recentactivitydata: any;
  activitydatanode: any;
  Events_dropdownList = [];
  Events_selectedItems = [];
  Events_dropdownSettings = {};
  export_csv_data: any = {}
  activitysearch:any;
  configListSelectedItem: any;
  additional_config_id: any;
  initialised: boolean = false

  public refreshStatus: any;

  SelectdaysDataList = [
  {
    id: '1',
    label: 'Sunday',
    isChecked: 'checked'
  },
  {
    id: '2',
    label: 'Monday',
    isChecked: ''
  },
  {
    id: '3',
    label: 'Tuesday',
    isChecked: ''
  },
  {
    id: '4',
    label: 'Wednesday',
    isChecked: ''
  },
  {
    id: '5',
    label: 'Thursday',
    isChecked: ''
  },
  {
    id: '6',
    label: 'Friday',
    isChecked: ''
  },
  {
    id: '7',
    label: 'Saturday',
    isChecked: ''
  },
]
Malware_Events_dropdownList = []
Malware_Events_selectedItems = [];
Malware_Events_dropdownSettings = {};
scriptform: FormGroup;
file_content:File;
file_name:any;
show_live_terminal_results=false;
script_type_name=''
script_type_value=''
  public temp_var: Object=false;
    hosts_addtags_val:any;
    hosts_removetags_val:any;
    pack_addtags_val:any;
    pack_removetags_val:any;
    queries_addtags_val:any;
    queries_removetags_val:any;
  StatusdtOptions: any = {};
  ActivitydtOptions: any = {};
  DefenderdtOptions: any = {};
  testdtOptions: DataTables.Settings = {};
  DefenderdtTrigger: Subject<any> = new Subject();
  ActivitydtTrigger: Subject<any> = new Subject();
  @ViewChild(DataTableDirective)
  dtElement: DataTableDirective;
  PreviousDataIds={}
  istabopen:boolean=false;
  list_of_QuarantineThreats=[]
  config_list_dropdownList = [];
  config_list_selectedItems: any;
  config_list_dropdownSettings = {}
  Live_terminal_command_id:any;
  public submit_button_disable_enable: boolean = false;
  role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess};
  compareAgentVersion:boolean;
  empty_data: boolean = false;
  openc2_id:number
  public screensize: any;
  showLoader: boolean = true;
  showLoaderRefresh: boolean = false;
  previousUrl: any;
  currentUrl: any;
  myRuleChart: any;
  detailPaneActive: boolean = false;
  isRecentActivityEmpty: boolean = false;
  isDisabled: boolean= false

  contentFileSizeError: boolean= false;
  maxFileSize: any = 2000000;
  packsCategoryDictionary = [];
  tempPacksCategoryDictionary = [];
  constructor(
    private _Activatedroute: ActivatedRoute,
    private commonapi: CommonapiService,
    private commonvariable: CommonVariableService,
    private router: Router,
    private http: HttpClient,
    private _location: Location,
    private titleService: Title,
    private toastr: ToastrService,
    private activity:ActivityComponent,
    private fb: FormBuilder,
    private el: ElementRef,
    private authorizationService: AuthorizationService,
    private tagsValidation:TagsValidationHandler
  ) {

   }
  toggle:boolean=false;
  @Input() hostData;

  ngOnInit() {
    this.hostState = history.state.hostState;
    if(this.hostData?.state == 1 || this.hostState == 1){
      this.isDisabled = true
    }
    this.initialised = true
    $.fn.dataTable.ext.errMode = 'none';
    $("#Quarantine_Threats_no_data").hide();
    $('.quarantine_loader').hide();
    this.screensize = window.innerWidth;
    this.titleService.setTitle(this.commonvariable.APP_NAME + " - " + "Hosts");
    this.sub = this._Activatedroute.paramMap.subscribe(params => {
      this.getFromActivityData();
      if (this.hostData != undefined || this.hostData != null) {
        this.id = this.hostData.id;
        this.detailPaneActive = true;
      }
      else {
        this.id = params.get('id');
      }

    });

    if((typeof environment.file_max_size == 'number') && environment.file_max_size> 0 && environment.file_max_size< 1073741824){
      this.maxFileSize = environment.file_max_size
    }
    let additional_config = this.commonapi.additional_config_api(this.id).subscribe(res => {
      this.additionaldata = res;
      if (this.additionaldata != undefined) {
        this.packs_count = Object.keys(this.additionaldata.data.packs).length;
        this.pack_name = this.additionaldata.data.packs;
        this.query_count = Object.keys(this.additionaldata.data.queries).length;
        this.query_names = this.additionaldata.data.queries;
        this.tags = this.additionaldata.data.tags;
        this.searchText;
        for(const i in this.pack_name){
          let ispresent = false;
          for(const j in this.packsCategoryDictionary){
            if(this.pack_name[i].category == this.packsCategoryDictionary[j]['category']){
              ispresent = true;
              if(this.pack_name[i].name in this.packsCategoryDictionary[j]['packs']){
                break;
              }else{
                this.packsCategoryDictionary[j]['packs'].push(this.pack_name[i].name);
              }
            }
          }
          if(ispresent == false){
            this.packsCategoryDictionary.push({'category':this.pack_name[i].category, 'packs': [this.pack_name[i].name]});
          }
        }
        this.tempPacksCategoryDictionary = this.packsCategoryDictionary;
        if (this.additionaldata.data.packs.length > 0) {
          this.getfirstpack_data();
        }

        if (this.additionaldata.data.queries.length > 0) {
          this.getfirst_data();
        }
      }

    });

    this.commonapi.recent_activity_count_api(this.id).subscribe(res => {
      this.nodesdata = res;
      if (this.nodesdata.data != undefined && this.nodesdata.data != null && this.nodesdata.data[0] != undefined) {
        this.activitynode = this.nodesdata.data;
        this.selected_query = this.activitynode[0]?.name
        this.query_name = this.activitynode[0]?.name;
        if (this.query_name == undefined || this.query_name == null) {
          this.query_name = ''
        }
        this.query_name = Array(this.query_name)
        this.activitycount = Object.keys(this.activitynode).length;

        this.searchText;

        this.defaultData = true;
        this.getFromActivityData();
        // this.Refresh_datatable()
        this.refreshActivityDatatable()
        this.isRecentActivityEmpty = false
      }
      else {
        this.isRecentActivityEmpty = true
      }
      this.showLoader = false;
    }, err => {
      this.showLoader = false;
    });

    this.Host_Alerted_rules();
    this.scriptform = this.fb.group({
      script_type: '',
      save_script: '',
      params: '',
      content: '',
      file_content: [''],
      // script_name:['', Validators.required]
    });

    this.config_list_dropdownSettings = {
      singleSelection: true,
      text: "Select config",
      selectAllText: 'Select All',
      unSelectAllText: 'UnSelect All',
      badgeShowLimit: 1,
      enableSearchFilter: true,
      classes: "config_list_dropdown"
    };

    this.Malware_Events_dropdownSettings = {
      singleSelection: true,
      text: "Select Malware Events",
      selectAllText: 'Select All',
      unSelectAllText: 'UnSelect All',
      enableSearchFilter: true,
      classes: "myclass custom-class"
    };

    this.Malware_Events_dropdownList = [
      { 'id': "1006,1116", 'itemName': "Malware found" },
      { 'id': "1007", 'itemName': "Malware action taken" },
      { 'id': "1008", 'itemName': "Malware action failed" },
      // { 'id': "2000,2002", 'itemName': "Malware definitions updated" },
      // ​{ 'id': "2001,2003", 'itemName': "Malware definitions update failed" },
      { 'id': "1000", 'itemName': "Malwareprotection scan started" },
      { 'id': "1001", 'itemName': "Malwareprotection scan completed" },
      { 'id': "1002", 'itemName': "Malwareprotection scan cancelled" },
      { 'id': "1003", 'itemName': "Malwareprotection scan paused" },
      { 'id': "1004", 'itemName': "Malwareprotection scan resumed" },
      { 'id': "1005", 'itemName': "Malwareprotection scan failed" },
      // { 'id': "1006", 'itemName': "Malwareprotection malware detected" },
      // { 'id': "1007", 'itemName': "Malwareprotection malware action taken" },
      // ​{ 'id': "1008", 'itemName': "Malwareprotection malware action failed" },
      { 'id': "1009", 'itemName': "Malwareprotection quarantine restore" },
      { 'id': "1010", 'itemName': "Malwareprotection quarantine restore failed" },
      { 'id': "1011", 'itemName': "Malwareprotection quarantine delete" },
      { 'id': "1012", 'itemName': "Malwareprotection quarantine delete failed" },
      { 'id': "1013", 'itemName': "Malwareprotection malware history delete" },
      { 'id': "1014", 'itemName': "Malwareprotection malware history delete failed" },
      { 'id': "1015", 'itemName': "Malwareprotection behavior detected" },
      // { 'id': "1116", 'itemName': "Malwareprotection state malware detected" },
      { 'id': "1117", 'itemName': "Malwareprotection state malware action taken" },
      { 'id': "1118", 'itemName': "Malwareprotection state malware action failed" },
      { 'id': "1119", 'itemName': "Malwareprotection state malware action critically failed" },
      { 'id': "1120", 'itemName': "Malwareprotection threat hash" },
      { 'id': "1150", 'itemName': "Malwareprotection service healthy" },
      { 'id': "1151", 'itemName': "Malwareprotection service health report" },
      { 'id': "2000", 'itemName': "Malwareprotection signature updated" },
      { 'id': "2001", 'itemName': "Malwareprotection signature update failed" },
      { 'id': "2002", 'itemName': "Malwareprotection engine updated" },
      { 'id': "2003", 'itemName': "Malwareprotection engine update failed" },
      { 'id': "2004", 'itemName': "Malwareprotection signature reversion" },
      { 'id': "2005", 'itemName': "Malwareprotection engine update platformoutofdate" },
      { 'id': "2006", 'itemName': "Malwareprotection platform update failed " },
      { 'id': "2007", 'itemName': "Malwareprotection platform almostoutofdate" },
      { 'id': "2010", 'itemName': "Malwareprotection signature fastpath updated" },
      { 'id': "2011", 'itemName': "Malwareprotection signature fastpath deleted" },
      { 'id': "2012", 'itemName': "Malwareprotection signature fastpath update failed" },
      { 'id': "2013", 'itemName': "Malwareprotection signature fastpath deleted all" },
      { 'id': "2020", 'itemName': "Malwareprotection cloud clean restore file downloaded" },
      { 'id': "2021", 'itemName': "Malwareprotection cloud clean restore file download failed" },
      { 'id': "2030", 'itemName': "Malwareprotection offline scan installed" },
      { 'id': "2031", 'itemName': "Malwareprotection offline scan install failed" },
      { 'id': "2040", 'itemName': "Malwareprotection os expiring" },
      { 'id': "2041", 'itemName': "Malwareprotection os eol" },
      { 'id': "2042", 'itemName': "Malwareprotection protection eol" },
      { 'id': "3002", 'itemName': "Malwareprotection rtp feature failure" },
      { 'id': "3007", 'itemName': "Malwareprotection rtp feature recovered" },
      { 'id': "5000", 'itemName': "Malwareprotection rtp enabled" },
      { 'id': "5001", 'itemName': "Malwareprotection rtp disabled" },
      { 'id': "5004", 'itemName': "Malwareprotection rtp feature configured" },
      { 'id': "5007", 'itemName': "Malwareprotection config changed" },
      { 'id': "5008", 'itemName': "Malwareprotection engine failure" },
      { 'id': "5009", 'itemName': "Malwareprotection antispyware enabled" },
      { 'id': "5010", 'itemName': "Malwareprotection antispyware disabled" },
      { 'id': "5011", 'itemName': "Malwareprotection antivirus enabled" },
      { 'id': "5012", 'itemName': "Malwareprotection antivirus disabled" },
      { 'id': "5100", 'itemName': "Malwareprotection expiration warning state" },
      { 'id': "5101", 'itemName': "Malwareprotection disabled expired state" },
    ];

    //Adding Recent Activity to Tab View
    this.Events_dropdownSettings = {
      singleSelection: false,
      text: "Select Events",
      selectAllText: 'Select All',
      unSelectAllText: 'UnSelect All',
      enableSearchFilter: true,
      badgeShowLimit: 1,
      classes: "myclass custom-class",
    };
    this.Events_dropdownList = [
      { "id": 1, "itemName": "File" },
      { "id": 2, "itemName": "Process" },
      { "id": 3, "itemName": "Remote Thread" },
      { "id": 4, "itemName": "Process Open" },
      { "id": 5, "itemName": "Removable Media" },
      { "id": 6, "itemName": "Image Load" },
      { "id": 7, "itemName": "Image Load Process Map" },
      { "id": 8, "itemName": "HTTP" },
      { "id": 9, "itemName": "SSL" },
      { "id": 10, "itemName": "Socket" },
      { "id": 11, "itemName": "DNS" },
      { "id": 12, "itemName": "DNS Response" },
      { "id": 13, "itemName": "Registry" },
      { "id": 14, "itemName": "Yara" },
      { "id": 15, "itemName": "Logger" },
      { "id": 16, "itemName": "File Timestamp" },
      { "id": 17, "itemName": "PeFile" },
      { "id": 18, "itemName": "Defender Events" },
      { "id": 19, "itemName": "Pipe Events" }
    ];

    // this.getFromActivityData();
    this.fetchData()
    this.refreshStatus =setInterval(()=>{
      this.fetchData()
    }, 30000);
    // this.Getdefenderlog();
  }
  get s() { return this.scriptform.controls; }

  private async fetchData() {
    const data = await this.commonapi.host_name_api(this.id).toPromise();
    this.data = data;
    if (this.data.status == "failure") {
      this.pagenotfound();
    }
    else {
      this.host_identifier = this.activitydata?.data?.host_identifier
      this.activitydata = data
      if (this.activitydata?.data?.id == this.id) {
        this.nodes = this.activitydata?.data?.node_info?.computer_name;
      }
      if (this.data.data.id == this.id) {
        this.nodes = this.data.data;
        this.node_id = this.nodes.id;
        this.network_info = this.nodes.network_info;
        this.host_identifier = this.nodes.host_identifier
        if (this.nodes.os_info != null) {
          this.osInfo = this.nodes.os_info;
          this.os_platform = this.nodes.os_info.platform;
          this.os_name = this.nodes.os_info.name;
        }
        this.hostDetails = this.nodes.host_details;
        if (this.hostDetails['extension_version']) {
          this.compareAgentVersion = compare(this.hostDetails['extension_version'], "3.0", '<')
        }
        if (this.nodes.platform == 'windows' && !this.hostDetails.hasOwnProperty('windows_security_products_status')) {
          this.hideDefender(msg.unableFetchMsg);
        }
        //Security Center is supported only on Windows 8 and above
        if (this.os_name.includes("Windows 7") || this.os_name.includes("Windows Server")) {
          this.hideDefender(msg.windowsErrorMsg);
        }
        else if(this.nodes.platform == 'windows' && this.hostDetails.hasOwnProperty('windows_security_products_status')&& !this.os_name.includes("Windows 7") && !this.os_name.includes("Windows Server")){
          this.showDefender()
        }
        this.windows_defender_status = this.hostDetails.windows_security_products_status;
        this.node_info = this.nodes.node_info;
        this.physical_memory = this.physical_memory_formate(this.nodes.node_info.physical_memory);
        this.currentdate = new Date();

        if (!this.hostDetails) {
          this.hostDetails = {};
        }

        if (!this.hostDetails['osquery_version']) {
          this.hostDetails['osquery_version'] = "-";
        }

        if (!this.hostDetails['extension_version']) {
          this.hostDetails['extension_version'] = "-";
        }
        if (this.nodes.last_checkin == null) {
          this.lastcheckin = ''

        } else {
          var lastCheckinUtc = moment.utc(this.nodes.last_checkin).format();
          this.lastcheckin = moment(lastCheckinUtc).fromNow();

        }


        if (this.nodes.enrolled_on == null) {
          this.enrolled = ''
        } else {
          // Formatting to ISO8601 spec for Safari+Chrome support
          const temp = this.nodes.enrolled_on.toString().replace(' ', 'T');
          this.enrolled = new Date(temp);
        }

        if (this.nodes.last_status == null) {
          this.laststatus = ''
        } else {
          var lastStatusUtc = moment.utc(this.nodes.last_status).format();
          this.laststatus = moment(lastStatusUtc).fromNow();
        }

        if (this.nodes.last_result == null) {
          this.lastresult = ''
        } else {
          var lastResultutc = moment.utc(this.nodes.last_result).format();
          this.lastresult = moment(lastResultutc).fromNow();
        }

        if (this.nodes.last_config == null) {
          this.lastconfig = ''
        } else {
          var lastConfigUtc = moment.utc(this.nodes.last_config).format();
          this.lastconfig = moment(lastConfigUtc).fromNow();
        }


        if (this.nodes.last_query_read == null) {
          this.lastqueryread = ''
        } else {
          var lastQueryReadUtc = moment.utc(this.nodes.last_query_read).format();
          this.lastqueryread = moment(lastQueryReadUtc).fromNow();
        }
        if (this.nodes.last_query_write == null) {
          this.lastquerywrite = ''
        } else {
          var lastQueryWriteutc = moment.utc(this.nodes.last_query_write).format();
          this.lastquerywrite = moment(lastQueryWriteutc).fromNow();
        }
      }
      if (this.nodes.platform == 'windows') {
        this.script_type_value = '2'
        this.script_type_name = 'PowerShell Script'
      } else {
        this.script_type_value = '4'
        this.script_type_name = 'Shell Script'
      }
    }

  }


    hideDefender(msg){
      $('.show_Manage_Defender').hide()
      $(".show_NotApplicable_Msg").show();
      $(".show_NotApplicable_Msg").html(msg);
    }
    showDefender(){
      $('.show_Manage_Defender').show()
      $(".show_NotApplicable_Msg").hide();
    }
    setDataHost(value){
      localStorage.setItem('path',value);
    }
    public getPreviousUrl() {
      return this.previousUrl;
    }
    goToAlerts(value, alertType) {
      this.router.navigateByUrl('/', {skipLocationChange: true}).then(()=>
      this.router.navigate(['/alerts'],{queryParams: { 'id': this.node_id, 'from':value,'alertType':alertType }}));
    }
    validDateFormat(value) {
      if (value) {
        let date = value.substring(0, 10);
        let time = value.substring(11, 19);
        let millisecond = value.substring(20)
        let date1 = date.split('-')[0];
        let date2 = date.split('-')[1];
        let date3 = date.split('-')[2];
        let validDate = date1 + '-' + date2 + '-' + date3 + ' ' + time;
        return validDate
      }

      return null;

    }
    Host_Alerted_rules(){
     let host_id =  this.id;
     let alertedrules=this.commonapi.Host_rules_api(host_id).subscribe(res => {
      this.alertlist = res;
      if(this.alertlist.status == "success"){
        this.alienvault = this.alertlist.data.sources.alienvault;
        this.ibmxforce = this.alertlist.data.sources.ibmxforce;
        this.rule = this.alertlist.data.sources.rule;
        this.ioc = this.alertlist.data.sources.ioc;
        this.virustotal = this.alertlist.data.sources.virustotal;
        var rules = this.alertlist.data.rules;
        var rule_name = []
        var rule_count = [];
        for(const i in rules){
          rule_name.push(rules[i].name)
          rule_count.push(rules[i].count)
        }
        if(rule_name.length==0){
          $('.top_rules').hide();
          $(document.getElementById('no-data-bar-chart-top_5_alerted_rules')).removeClass('display-none')
          $(document.getElementById('no-data-bar-chart-top_5_alerted_rules')).html("No Rule Based Alerts");
       }else{
          this.load_top_rules_graph(rule_name,rule_count)
          $('.top_rules').show();
          if(!$(document.getElementById('no-data-bar-chart-top_5_alerted_rules')).hasClass('display-none')){
            $(document.getElementById('no-data-bar-chart-top_5_alerted_rules')).addClass('display-none')
          }

       }
      }

    });
    }

    load_top_rules_graph(rule_name,rule_count){
      if(this.myRuleChart){
        this.myRuleChart.destroy()
        this.myRuleChart = new Chart('alerted_rules', {
        type: 'bar',
        data: {
            labels:rule_name,
            datasets: [{
                data: rule_count,
                backgroundColor: [
                          "#2A6D7C",
                          "#A2D9C5",
                          "#F79750",
                          "#794F5D",
                          "#6EB8EC"
                      ],
                barPercentage: 0.5,
            }]
        },
        options: {
          tooltips:{
            intersect : false,
            mode:'index'
            },
            responsive: true,
          // maintainAspectRatio: false,
          legend: {
            display: false
          },
          plugins: {
            labels: {
              render: () => {}
            }
          },
          scales: {
            offset:false,
            xAxes: [{
              barThickness: 30,
              gridLines: {
                  offsetGridLines: true,
                  display : false,
              },
              ticks: {
                callback: function(label, index, labels) {
                  var res = label.substring(0,2)+"..";
                  return res;
                },
                minRotation: 45
              }
          }],
          yAxes: [{
            ticks: {
                beginAtZero: true,
                display: false,
            },
            gridLines: {
              drawBorder: false,
          }
        }]
          },
        }
      });
    }
    else{
      this.myRuleChart = new Chart('alerted_rules', {
        type: 'bar',
        data: {
            labels:rule_name,
            datasets: [{
                data: rule_count,
                backgroundColor: [
                          "#2A6D7C",
                          "#A2D9C5",
                          "#F79750",
                          "#794F5D",
                          "#6EB8EC"
                      ],
                barPercentage: 0.5,
            }]
        },
        options: {
          tooltips:{
            intersect : false,
            mode:'index'
            },
            responsive: true,
          // maintainAspectRatio: false,
          legend: {
            display: false
          },
          plugins: {
            labels: {
              render: () => {}
            }
          },
          scales: {
            offset:false,
            xAxes: [{
              barThickness: 30,
              gridLines: {
                  offsetGridLines: true,
                  display : false,
              },
              ticks: {
                callback: function(label, index, labels) {
                  var res = label.substring(0,2)+"..";
                  return res;
                },
                minRotation: 45
              }
          }],
          yAxes: [{
            ticks: {
                beginAtZero: true,
                display: false,
            },
            gridLines: {
              drawBorder: false,
          }
        }]
          },
        }
      });
    }
    }

    onOptionsSelected(event:any){
     if(event.target.value == 1){
      let modal = document.getElementById("myModal");
      modal.style.display = "block";
      this.showdata(undefined);
     }else if(event.target.value == 2){
     this.node_id = this.nodes.id;
     this.cpt_restart(this.node_id);
     }

    }

  onselectoption(value){
    if(value == 1){
     let modal = document.getElementById("myModal");
     modal.style.display = "block";
     this.showdata(undefined);
    }else if(value == 2){
    this.cpt_restart(this.host_identifier);
    }
   }

close() {
  let modal = document.getElementById("myModal");
  modal.style.display = "none";
  this.actionselect = 0;
 }
    showdata(n){

      this.commonapi.view_config_api(this.id).subscribe(res =>{
        this.additional_config_data =res['config'].name;
        this.additional_config_id = res['config'].id ? res['config'].id : 'Any'
      this.toggle=false;
      setTimeout(()=>{
        this.editorOptions = new JsonEditorOptions();
        this.editorOptions.mode = 'view';
        this.alerted_data_json=res['data'];
        this.toggle=true;
      }, 100);
    })
      this.config_list_dropdownList=[]
      this.config_list_dropdownList.push({value: 'Any', description: 'Select Config'})
      this.commonapi.configs_api().subscribe((res: any) => {
        if(!['windows','darwin'].includes(this.nodes['platform'])){
          this.nodes['platform'] = 'linux'
        }
      for (const i in res.data[this.nodes['platform']]){
        this.config_list_dropdownList.push({value: res['data'][this.nodes['platform']][i]['id'], description: i});
      }
      this.configListSelectedItem = this.additional_config_id
      })
    }
    Assign_config(){
      if(this.additional_config_id == this.configListSelectedItem){
        this.get_swal_error_message("Selected Config is already assigned")
      }
      else{
        var payload = {"host_identifiers":this.host_identifier}
        if(this.config_list_selectedItems){
        this.commonapi.asign_config_to_hosts(this.config_list_selectedItems['id'],payload).subscribe(res=>{
          if(res["status"]=="success"){
            this.close()
            Swal.fire({
              icon: 'success',
              text: res["message"]
              })
          }else{
            this.get_swal_error_message(res["message"])
          }
          })
        }else{
          this.close()
          this.get_swal_error_message("Please select config")
        }
      }
    }
    get_swal_error_message(message){
      Swal.fire({
        icon: 'warning',
        text: message
        })
    }


    /*
    This function convert bytes into  system physical_memory format
    */

    physical_memory_formate(bytes){
      let sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
      if (bytes == 0)
        return '0 Byte';
      if( parseInt(bytes) < 0 )
        return -1
      this.byte_value = Math.floor(Math.log(bytes) / Math.log(1024));
      return Math.round(bytes / Math.pow(1024, this.byte_value)) + ' ' + sizes[this.byte_value];
    }

    refreshData(){
        let products=this.commonapi.host_name_api(this.id).subscribe(res => {
          this.data = res;
          if(this.data.data.id == this.id){
              this.nodes = this.data.data;
              this.node_id = this.nodes.id;
              this.network_info = this.nodes.network_info;
              this.node_info = this.nodes.node_info;
              this.currentdate = new Date();
              if(this.nodes.last_checkin==null){
                this.lastcheckin=''
              }else{
                var lastCheckinUtc = moment.utc(this.nodes.last_checkin).format();
                this.lastcheckin = moment(lastCheckinUtc).fromNow();
              }
              if(this.nodes.enrolled_on==null){
                this.enrolled=''
              }else{
                // Formatting to ISO8601 spec for Safari+Chrome support
                const temp = this.nodes.enrolled_on.toString().replace(' ', 'T');
                this.enrolled = new Date(temp);
              }

              if(this.nodes.last_status==null){
                this.laststatus=''
              }else{
                var lastStatusUtc = moment.utc(this.nodes.last_status).format();
                this.laststatus = moment(lastStatusUtc).fromNow();
              }

              if(this.nodes.last_result==null){
                this.lastresult=''
              }else{
                var lastResultUtc = moment.utc(this.nodes.last_result).format();
                this.lastresult = moment(lastResultUtc).fromNow();
              }

              if(this.nodes.last_config==null){
                this.lastconfig=''
              }else{
                var lastConfigUtc = moment.utc(this.nodes.last_config).format();
                this.lastconfig = moment(lastConfigUtc).fromNow();
              }


              if(this.nodes.last_query_read==null){
                this.lastqueryread=''
              }else{
                var lastQueryReadUtc = moment.utc(this.nodes.last_query_read).format();
                this.lastqueryread = moment(lastQueryReadUtc).fromNow();
              }
              if(this.nodes.last_query_write==null){
                this.lastquerywrite=''
              }else{
                var lastQueryWriteUtc = moment.utc(this.nodes.last_query_write).format();
                this.lastquerywrite = moment(lastQueryWriteUtc).fromNow();
              }
          }
        })
        this.responce_action = this.commonapi.response_action(this.id).subscribe(res =>{
          if(res["status"]=="success"){
          this.action_status = res;
          this.endpoint = this.action_status.endpointOnline;
          this.responseenabled = this.action_status.responseEnabled;
          }else{
            this.responseenabled='Failed'
          }
      },(error) => {                              //Error callback
        if([500,502].includes(error.status)){
          this.responseenabled='Failed'
        }else if(error.status==401){
          localStorage.removeItem('reset_password');
          localStorage.removeItem('roles');
          localStorage.removeItem('all_roles');
          localStorage.removeItem('token');
          this.router.navigate(['./authentication/login']);
        }
      })
        // this.getData(false);
        //Passing the false flag would prevent page reset to 1 and hinder user interaction

    }
    @HostListener('unloaded')
    ngOnDestroy() {
      console.log('ngOnDestroy')
        clearInterval(this.interval)
        window.clearInterval(this.interval);
        clearInterval(this.defenderTimeout)
        clearTimeout(set_time_out)
        clearInterval(this.refreshStatus)
   }

    cpt_restart(host_id){
      swal({
        title: "Are you sure?",
        text: "You want to restart the agent!",
        icon: "warning",
        buttons: ["Cancel", 'Yes! Restart it'],
        closeOnClickOutside: false,
        dangerMode: true,
      })
      .then((willDelete) => {
        if (willDelete) {
          let products=this.commonapi.cpt_restart_api(host_id).subscribe(res => {
            this.data = res;
            if(this.data.status =='success'){
            swal({
              icon: 'success',
              title: 'Restart Initiated!',
              text: 'initiated agent restart command',
              buttons: [false],
             timer: 2000,
             })
            }else{
              swal({
                icon: 'error',
                title: 'Error!',
                text: 'Error initiating agent restart command',
               timer: 2000
                })
            }
          })

        }
      });
    }

  getBy_packId(pack_name) {
    this.selectedItem=pack_name
    for (const i in this.additionaldata.data.packs) {
      if (this.additionaldata.data.packs[i].name == pack_name) {
        this.pack_data = this.additionaldata.data.packs[i]
      }
    }
  }
  getfirstpack_data() {
    this.pack_data = this.additionaldata.data.packs[0];
    this.selectedItem=this.pack_data.name
  }

  ngAfterViewInit(): void {
    this.DefenderdtTrigger.next();
    this.ActivitydtTrigger.next();
  }

  getById(queryId) {
    for (const i in this.additionaldata.data.queries) {
      if (this.additionaldata.data.queries[i].id == queryId) {
        this.querydata = this.additionaldata.data.queries[i]
        this.queryid = queryId
      }
    }
  }

  getfirst_data() {
    this.querydata = this.additionaldata.data.queries[0];
    this.queryid = this.querydata.id
  }

  runAdHoc(queryId) {
    this.router.navigate(['live-query/', queryId]);
  }

  redirect(pack) {
    this.router.navigate(['/tags']);
  }


  hosts_addTag(tags, node_id) {
    this.commonapi.hosts_addtag_api(node_id, tags.toString()).subscribe(res => {
      this.hosts_addtags_val = res;
    });
  }
  hosts_removeTag(event, node_id) {
    this.commonapi.hosts_removetags_api(node_id, event).subscribe(res => {
      this.hosts_removetags_val = res;
    });

  }

  pack_addTag(test, id) {
    this.commonapi.packs_addtag_api(id, test.toString()).subscribe(res => {
      this.pack_addtags_val = res;

    });
  }
  pack_removeTag(pack_id,event) {
    this.commonapi.packs_removetags_api(event, pack_id).subscribe(res => {
      this.pack_removetags_val = res;
    });

  }

  queries_addTag(tags, query_id) {
    this.commonapi.queries_addtag_api(query_id, tags.toString()).subscribe(res => {
      this.queries_addtags_val = res;

    });
  }
  queries_removeTag(event, query_id) {
    this.commonapi.queries_removetags_api(query_id, event).subscribe(res => {
      this.queries_removetags_val = res;
    });

  }

  goBack() {
    this._location.back();
  }
  get_status_log_data(){
    var that=this;
    this.StatusdtOptions = {
      pagingType: 'full_numbers',
      pageLength: 10,
      serverSide: true,
      processing: true,
      searching: true,
      dom: "<'row'<'col-sm-12'f>>" +
      "<'row'<'col-sm-12'tr>>" +
      "<'row node-table-controls table-controls'<'col-sm-6 d-flex align-items-center justify-content-start'li><'col-sm-6'p>>",
      buttons: [
        {
          text: 'Export',
          attr:  {id: 'IdExport'},
          action: function ( e, dt, node, config ) {
            that.exportstatuslog();
          },
        },
      ],
      "language": {
        "search": "Search: ",
        "sInfo" : "Showing _START_ to _END_ of <b>_TOTAL_</b> entries",
        "lengthMenu": "<ng-container class=custom-pagination-length>Results per page: _MENU_</ng-container>",
      },
      ajax: (dataTablesParameters: any, callback) => {
        var body = dataTablesParameters;
        body['limit']=body['length'];
        if(body.search.value!= ""){
          body['searchterm']=body.search.value;
        }
        let host_id = this.id;
        var body = dataTablesParameters;
        body['limit'] = body['length'];
        body['node_id'] = host_id;
        this.http.post<DataTablesResponse>(environment.api_url+"/hosts/status_logs", body, { headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res =>{
          this.log_status = res;
          this.log_data = this.log_status.data.results;
          if(this.log_data.length >0 &&  this.log_data!=undefined)
          {

            // $("#DataTables_Table_0_info").
            $('.dataTables_paginate').show();
            $('.dataTables_info').show();


          }
          else{
            if(body.search.value=="" || body.search.value == undefined)
            {
              this.errorMessageLogs="No Data Found";
              var Export_Element = document.getElementById("IdExport");
              Export_Element?.classList.add("disabled");
            }
            else{
              this.errorMessageLogs="No Matching Record Found";
            }

            $('.node-table-controls > * >.dataTables_paginate').hide();
            $('.node-table-controls > * >.dataTables_info').hide();

          }

          callback({
            recordsTotal: this.log_status.data.count,
            recordsFiltered: this.log_status.data.count,
            data: []
          });
        });
      },
      ordering: false,
      columns: [{ data: 'line' }, { data: 'message' }, { data: 'severity' }, { data: 'filename' },{ data: 'created' },{ data: 'version' }]
    }
  }
  ShowProgess:boolean = false;
  exportstatuslog(){
    this.ShowProgess = true;
    let host_id = this.id;
    var payload={
      "node_id":host_id
    }
    this.commonapi.hoststatuslogexport(payload).subscribe(res => {
      if(res['status']){
        var taskid = res['data'].task_id;
        Wssl = new WebSocket(Statuslog_Live_Url);
        this.StatusLogSocketQuery(taskid);
        window.addEventListener('offline', () =>   this.toastr.error('Network disconnected!.\n You may  not receive any pending results. Try sending the query again\ once connected'));
      }
    });

  }
  StatusLogSocketQuery(queryId){
    Wssl.onopen = function () {
      Wssl.send(queryId);
    };
    var that = this;
    Wssl.onmessage = function (event) {
      try {
        var data = event.data;
        if (data instanceof Blob) {
          var reader = new FileReader();
          Wssl.close() /* Closing the socket once we get data from live query */
          reader.addEventListener('loadend', (event: Event) => {
            const text = reader.result as string;
            var response_data = JSON.parse(text);
            if(response_data.download_path){
              that.ShowProgess = false;
              window.location.href = response_data.download_path;
              swal("File Download Completed", {
                icon: "success",
                buttons: [false],
                timer: 2000
              });
            }
          });
          reader.readAsText(data);
        }
      } catch (err) {
        console.log(err);
      }
    };
  }

  status_log_tab(){
    this.status_log_checkbox = false;
  }
  toggleEditable(event) {
    if ( event.target.checked ) {
      this.status_log_checkbox = true;
      this.get_status_log_data();
   }else{
    this.status_log_checkbox = false;
   }
  }

  pagenotfound() {
      this.router.navigate(['/pagenotfound']);
  }

    isvalidtimepicker(time){
      if(typeof time !== 'undefined'){
        return true;
      }
      else{
        return false;
      }
    }
    action(event): void {
      event.stopPropagation();
    }



  closedefender() {
   let modal = document.getElementById("successModal");
   modal.style.display = "none";
  }
  Refresh_datatable(){
    this.DefenderdtTrigger.next();
    this.ActivitydtTrigger.next();
  }
  refreshActivityDatatable(){
    this.ActivitydtTrigger.next();
  }

  EmptyPaginationIds(){
    this.PreviousDataIds={}
    NextDataId=0
  }
  onItemSelect(item:any){
    this.EmptyPaginationIds()
    this.Refresh_datatable()
  }
  OnItemDeSelect(item:any){
   this.EmptyPaginationIds()
    this.Refresh_datatable()
  }
 onSelectAll(items: any){
  }
 onDeSelectAll(items: any){
  this.EmptyPaginationIds()
  this.Malware_Events_selectedItems=[]
  this.Refresh_datatable()
}

get_swal_message(type,message){
  Swal.fire({
    icon: type,
    text: message,
    })
}

resetFile(){
  this.scriptform.controls['file_content'].reset();
  this.file_name = ''
}


onChange(text) {
this.live_test_code=text
}
get_script_type(type){
  this.script_type_name=type
}

onItemSelect_config(value, description) {

  let item= {
    id: value,
    itemName: description
  }
  this.config_list_selectedItems = item
}
OnItemDeSelect_config(item: any) {
  console.log(item);
}
onDeSelectAll_config(items: any) {
  this.config_list_selectedItems=[]
}
Alertmessage(type,title,message){
  Swal.fire({
    title:title,
    icon: type,
    text: message,
    })
}
closeModal(modalId){
  let modal = document.getElementById(modalId);
  modal.style.display = "none";
  $('.modal-backdrop').remove();
}
openModal(modalId){
  ($('#' + modalId) as any).modal('show')
  $('.modal-backdrop').remove();
}

//Recent Activity
getFromActivityData() {
  var that=this;
  this.ActivitydtOptions = {
    pagingType: 'simple',
    pageLength: 10,
    scrollX: false,
    scrollY: 480,
    serverSide: true,
    processing: true,
    searching: true,
    dom: '<"pull-right"B><"pull-right"f><"pull-left">t<"align-center d-flex justify-content-between row table-controls"<"col-sm-6 d-flex align-items-center table-controls-li"li><"col-sm-6 d-flex align-items-center justify-content-end paginate_button-processing"p>>',
    buttons: [
      {
        text: 'CSV',
        attr:  {id: 'IdExport'},
        className: 'btn btn-csv',
        action: function ( e, dt, node, config ) {
          that.get_csv_data();
        },
      },
    ],
    "language": {
      "search": "Search: ",
      "info" : "Showing _START_ to _END_ of <b>_TOTAL_</b> entries",
      "lengthMenu": "<ng-container class=custom-pagination-length>Results per page: _MENU_</ng-container>",
    },
    ajax: (dataTablesParameters: any, callback) => {
      $('.recentActivityLoader').show();
      let node_id = this.id;
      var body = dataTablesParameters;
      PaginationIndex=body['start']
      ActivityPaginationLength = body['length']
      if(PaginationIndex>TempIndex)   //checking next page index
      {
        body['start']=NextDataId
      }
      else if (PaginationIndex<TempIndex)  //checking Previous page index
      {
        body['start']=this.PreviousDataIds[PaginationIndex]
      }
      if(ActivityPaginationLength != ActivityTempLength){
        dataTablesParameters.start = 0
        body['start'] = 0
        var table = $("#activity_table").DataTable();
        table.page(0)
        PaginationIndex = 0
      }
      SelectedNodeID = body['start'];
      TempIndex = PaginationIndex;
      ActivityTempLength = ActivityPaginationLength;
      body['limit'] = body['length'];
      body['node_id'] = node_id;
      if (!this.query_name && !this.queryname){
        return;
      }
      if (this.defaultData) {
        body['query_name'] = this.query_name;
        this.ActivityselectedItem = this.query_name;
        this.queryname = this.query_name;

      } else {
        body['query_name'] = this.queryname;
      }
      if(body.search.value!= ""  &&  body.search.value.length>=1)
      {
        body['searchterm']=body.search.value;
      }
      if(body['searchterm']==undefined){
        body['searchterm']="";
      }
      if(this.Events_selectedItems.length>0){
        var eventids=''
        for(const eventid in this.Events_selectedItems){
          eventids=eventids + ',' + this.Events_selectedItems[eventid].id
        }
        body["column_name"]="eventid",
        body["column_value"]=eventids
      }
      this.http.post<DataTablesResponse>(environment.api_url + "/hosts/recent_activity", body, {headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).toPromise().then(res => {
        if(res.data){
        $('.recentActivityLoader').hide();
        this.recentactivitydata = res;
        this.activitydatanode = this.recentactivitydata?.data?.results;
        for(const id in this.activitynode){
          if(this.activitynode[id]?.name==this.queryname){
            this.activitynode[id].count = res.data['total_count']
          }
        }
        for (var v = 0; v < this.activitydatanode?.length; v++) {
          if (this.activitydatanode[v]?.columns != '') {
            this.activitydatanode[v].columns = this.activitydatanode[v].columns;
          }


        }
        if(this.activitydatanode?.length >0 &&  this.activitydatanode!=undefined)
          {
            this.PreviousDataIds[PaginationIndex]=(this.activitydatanode[0].id)+1
            NextDataId=(this.activitydatanode[this.activitydatanode.length - 1]).id
            $('.dataTables_paginate').show();
            $('.dataTables_info').show();
          }
          else{
            this.activitydatanode =null;
            if(body.search.value=="" || body.search.value == undefined)
            {
              this.errorMessage="No Data Found";
            }
            else{
              this.errorMessage="No Matching Record Found";
            }

            $('.dataTables_paginate').hide();
            $('.dataTables_info').hide();

          }
        // this.temp_var=true;
        callback({
          recordsTotal: this.recentactivitydata.data.categorized_count,
          recordsFiltered: this.recentactivitydata.data.count,

          data: [],
          cache: false,
        });
        }
        else{
          return;
        }
      });
    },
    ordering: false,
    columns: [{ data: 'columns' }],
  };
  $(document).on( 'click', '.paginate_button', function (e) {
    if(!(e.currentTarget.className).includes('disabled')){
        $('.paginate_button-processing .paginate_button.next').addClass('disabled');
        $('.paginate_button-processing .paginate_button.previous').addClass('disabled');
    }})
}
get_csv_data() {
  this.export_csv_data["host_identifier"] = this.host_identifier;
  this.export_csv_data["query_name"] = this.queryname;
  if(this.Events_selectedItems.length>0){
    var eventids=''
    for(const eventid in this.Events_selectedItems){
      eventids=eventids + ',' + this.Events_selectedItems[eventid].id
    }
    this.export_csv_data["column_name"]="eventid",
    this.export_csv_data["column_value"]=eventids
  }
  this.commonapi.recent_activity_search_csv_export(this.export_csv_data).subscribe(blob => {
    saveAs(blob, this.queryname+"_"+this.host_identifier+'.csv');

  })
}
getByActivityId(event, newValue, qryname, node_id): void {
  this.Events_selectedItems=[]
   if(this.selected_query==qryname){
   }else{
    this.ActivityselectedItem = newValue;
    this.queryname = qryname;
    this.defaultData = false;
    this.Refresh_datatable()
    this.selected_query=qryname;
  }
    this.PreviousDataIds={}
    NextDataId=0
  }
initialise_val(eventdata,data_process_guid) {

  const menuItems = [
    {
      title: 'Show More',
      action: (elm, d, i) => {

        if (d.count >= 20) {
          call_more(d);

        }
        // TODO: add any action you want to perform
      }
    }
  ];
  d3.contextMenu = function (menu, openCallback) {
    // create the div element that will hold the context menu
    d3.selectAll('.d3-context-menu').data([1])
      .enter()
      .append('div')
      .attr('class', 'd3-context-menu');

    // close menu
    d3.select('body').on('click.d3-context-menu', function () {
      d3.select('.d3-context-menu').style('display', 'none');
    });

    // this gets executed when a contextmenu event occurs
    return function (data, index) {
      if (!(data.node_type=='action' && data.count>20)){
        return;
      }
      var elm = this;

      d3.selectAll('.d3-context-menu').html('');
      var list = d3.selectAll('.d3-context-menu').append('ul');
      list.selectAll('li').data(menu).enter()
        .append('li')
        .html(function (d) {
          return (typeof d.title === 'string') ? d.title : d.title(data);
        })
        .on('click', function (d, i) {
          d.action(elm, data, index);
          d3.select('.d3-context-menu').style('display', 'none');
        });

      // the openCallback allows an action to fire before the menu is displayed
      // an example usage would be closing a tooltip
      if (openCallback) {
        if (openCallback(data, index) === false) {
          return;
        }
      }

      // display context menu
      d3.select('.d3-context-menu')
        .style('left', (d3.event.pageX - 2) + 'px')
        .style('top', (d3.event.pageY - 2) + 'px')
        .style('display', 'block');

      d3.event.preventDefault();
      d3.event.stopPropagation();
    };
  };
  var token_value = localStorage.getItem('token');
  var eid = eventdata.columns.eid;

  var jsonObjectOfActions = {
    "FILE_": "target_path",
    "PROC_": "path",
    "HTTP_": "remote_address",
    "SOCKET_": "remote_address",
    "IMAGE_": "image_path",
    "TLS_": "issuer_name",
    "REG_":"target_name",
    "DNS_":"domain_name"
  }

  var margin = {top: 20, right: 120, bottom: 20, left: 150},
    width = 960 - margin.right - margin.left,
    height = 800 - margin.top - margin.bottom;

  var i = 0,
    duration = 750;

  var tree = d3.layout.tree()
    .size([height, width]);
  var diagonal = function link(d) {
    return "M" + d.source.y + "," + d.source.x
      + "C" + (d.source.y + d.target.y) / 2 + "," + d.source.x
      + " " + (d.source.y + d.target.y) / 2 + "," + d.target.x
      + " " + d.target.y + "," + d.target.x;
  };

  var root;
  var id = this.id;
  var svg = d3.select("#d3-graph-2").append("svg")
    .attr("width", width + margin.right + margin.left)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
  var alert_process_guid;
  if (eventdata.columns.action == 'PROC_TERMINATE') {
    alert_process_guid = data_process_guid;
  } else {
    alert_process_guid = data_process_guid;
  }
  let ajaxAlertData = {
      "process_guid":alert_process_guid,
      "node_id":this.id,

  }
  $.ajax({
    type: "POST", //rest Type
    dataType: 'json', //mispelled
    url: environment.api_url + "/alerts/process",
    async: false,
    headers: {
      "content-type": "application/json",
      "x-access-token": token_value
    },
    data: JSON.stringify(ajaxAlertData),
    success: function (msgdata) {
      var name=data_process_guid;
      var data={};
      var event_data=eventdata.columns;
      if(event_data.hasOwnProperty('parent_process_guid')&&event_data['parent_process_guid']==data_process_guid){
        name=event_data['parent_path'];
        data['process_guid']=data_process_guid;
        data['path']=name;
      }
      else if(event_data.hasOwnProperty('process_guid')&&event_data['process_guid']==data_process_guid){
        if(!event_data.hasOwnProperty('parent_process_guid')){
          name=event_data['process_name'];
          data['process_guid']=data_process_guid;
          data['process_name']=name;

        }else{
          name=event_data['path'];
          data=event_data;
        }
      }
      root = msgdata.data;
      root['data']=data;
      root['name']=name;
      root['path']=name;
      create_graph(root);
    }
  });

  function create_graph(root) {
    root.x0 = height / 2;
    root.y0 = 0;
    root.children = root.all_children;
    root.children.forEach(function (d) {
      if (!d.hasOwnProperty('children')) {
        collapse(d);
      }
      d.hidden = false;
    });
    root.hidden = false;
    update(root);
    blinkNode();
    d3.select(self.frameElement).style("height", "800px");
  }

  function update(source) {
    // Compute the new tree layout.
    var nodes = tree.nodes(root).filter(function (d) {
        return !d.hidden;
      }).reverse(),
      links = tree.links(nodes);

    // Normalize for fixed-depth.
    nodes.forEach(function (d) {
      d.y = d.depth * 180;
    });

    // Update the nodes…
    var node = svg.selectAll("g.node")
      .data(nodes, function (d) {
        return d.id || (d.id = ++i);
      });
    // Enter any new nodes at the parent's previous position.
    var nodeEnter = node.enter().append("g")
      .attr("class", function (d) {
        if (d.hasOwnProperty("data") && d.data.eid == eid) {
          return "node ";
        }
        return "node";
      })

      .attr("transform", function (d) {
        return "translate(" + source.y0 + "," + source.x0 + ")";
      })


      .on('click', function (d, i) {
        selectedNode(d);

        if ((d.node_type == 'action' || d.data.action == 'PROC_CREATE') && !d.hasOwnProperty("fetched")) {
          callChild(d);

        } else {
          click(d);
        }
      })
      .on('contextmenu', d3.contextMenu(menuItems));


    nodeEnter.append("circle")
      .attr("r", 4.5)
      .style("fill", function (d) {

        if ((d.node_type == 'action' || d.hasOwnProperty("has_child")) && !d.hasOwnProperty("children") && !d.hasOwnProperty("_children") && !d.hasOwnProperty("all_children")) {
          d._children = [];


          return "lightsteelblue";
        } else {
          return d._children ? "lightsteelblue" : "#fff";
        }
      });

    nodeEnter.append("text")
      .attr("x", function (d) {
        return d.children || d._children ? -10 : 10;
      })
      .attr("dy", ".35em")
      .attr("text-anchor", function (d) {
        return d.children || d._children ? "end" : "start";
      })
      .text(function (d) {
        let title= getTitle(d)
        if(title.length> 24){
          return title.substr(0, 21).concat("...");
        }
        else
          return title
      })
      .style("fill-opacity", 1e-6);


    nodeEnter.append("title")
      .text(function (d) {
        return getTitle(d);
      });
    // Transition nodes to their new position.
    var nodeUpdate = node.transition()
      .duration(duration)
      .attr("transform", function (d) {
        return "translate(" + d.y + "," + d.x + ")";
      });

    nodeUpdate.select("circle")
      .attr("r", 4.5)
      .style("fill", function (d) {
        return d._children ? "lightsteelblue" : "#fff";
      });

    nodeUpdate.select("text")
      .style("fill-opacity", 1);

    // Transition exiting nodes to the parent's new position.
    var nodeExit = node.exit().transition()
      .duration(duration)
      .attr("transform", function (d) {
        return "translate(" + source.y + "," + source.x + ")";
      })
      .remove();

    nodeExit.select("circle")
      .attr("r", 4.5);

    nodeExit.select("text")
      .style("fill-opacity", 1e-6);

    // Update the links…
    var link = svg.selectAll("path.link")
      .data(links, function (d) {
        return d.target.id;
      });

    // Enter any new links at the parent's previous position.
    link.enter().insert("path", "g")
      .attr("class", "link")
      .attr("d", function (d) {

        var o = {x: source.x0, y: source.y0};
        return diagonal({source: o, target: o});
      }).attr("stroke", function (d) {
      return linkColor(d.target);
    });

    // Transition links to their new position.
    link.transition()
      .duration(duration)
      .attr("d", diagonal);

    // Transition exiting nodes to the parent's new position.
    link.exit().transition()
      .duration(duration)
      .attr("d", function (d) {
        var o = {x: source.x, y: source.y};
        return diagonal({source: o, target: o});
      })
      .remove();

    // Stash the old positions for transition.
    nodes.forEach(function (d) {
      d.x0 = d.x;
      d.y0 = d.y;
    });
    // node.on('contextmenu', d3.contextMenu(menuItems));
  }

  function click(d) {
    if (d.children) {
      d._children = d.children;
      d.children = null;
      if (d._children) {
        d._children.forEach(function (n) {
          n.hidden = true;
        });
        if (d.parent) {
          d.parent.children = d.parent.all_children;
          d.parent.children.forEach(function (n) {
            n.hidden = false;
          });
        }
      }
    } else {
      d.children = d._children;
      d._children = null;
      if (d.children) {
        d.children.forEach(function (n) {
          n.hidden = false;
        });

        if (d.parent) {
          d.parent.children = [d,];
          d.parent.children.filter(function (n) {
            return n !== d;
          }).forEach(function (n) {
            n.hidden = true;
          });
        }
      }
    }
    update(d);
  }

  function collapse(d) {
    if (d.children) {
      d.all_children = d.children;
      d._children = d.children;
      d._children.forEach(collapse);
      d.children = null;
      d.hidden = true;
    }
  }

  function blinkNode() {
    setInterval(function () {
      $('.blink-node').fadeTo('slow', 0.1).fadeTo('slow', 5.0);
    }, 1000);


  }

  function linkColor(link) {

    var action_colors = {
      "DNS_RESPONSE": "#fd7e14",
      "DNS_": "#007bff",
      "FILE_": "#dc3545",
      "PROC_": "#ffc107",
      "SOCKET_": "#28a745",
      "HTTP_": "#6c757d",
      "REG_": "#0000FF",
      "TLS_": "#20c997",
      "IMAGE_": "#7F007F",
    }
    for (var jsonObject in jsonObjectOfActions) {
      if (link.data && 'action' in link.data && link.data.action.includes(jsonObject)&& action_colors.hasOwnProperty(jsonObject)) {
        return action_colors[jsonObject];
      } else {
        if (link.node_type == 'action' && 'action' in link && link.action.includes(jsonObject) && action_colors.hasOwnProperty(jsonObject)) {
          return action_colors[jsonObject];
        }
      }
    }
    return "#0000FF";

  }

  function getTitle(d) {
    var name = d.name;
    if (d.node_type != 'action') {
      for (var jsonObject in jsonObjectOfActions) {
        if (d.data && 'action' in d.data && d.data.action.includes(jsonObject)) {
          let tempValue = jsonObjectOfActions[jsonObject];

          name = d.data[tempValue];
          if (d.data.action.includes("SOCKET")) {
            name = name + ":" + d.data.remote_port;
          }
          break;
        }
      }
    } else {
      name = name + "(" + d.count + ")";
    }
    if (name) {
      var lastlength = name.lastIndexOf('\\');
      var filter_process_name = name.substring(lastlength + 1);
      if (filter_process_name==''){
        var url = name.split( '\\' );
        if(url.length>=2){
          filter_process_name = url[ url.length - 2 ] ;
        }
      }
    }
    return filter_process_name;
  }

  function callChild(d) {

    if (d.hasOwnProperty("fetched") || d.hasOwnProperty("fetching")) {
      return
    }
    call_more(d);


  }

  function call_more(d) {
    d.fetching=true;
    if ((d.process_guid) && (d.node_type === 'action')) {

      let token_val = localStorage.getItem('token');
      let url_get_events_by_action_and_pgid = environment.api_url + '/alerts/process/child';
      let child_ajaxData = {
        "process_guid": d.process_guid,
        "action": d.action,
        "last_time": d.last_time,
        "node_id":id,
      }

      get_events_by_action_and_pgid();

      function get_events_by_action_and_pgid() {
        $.ajax({
          url: url_get_events_by_action_and_pgid,
          contentType: "application/json",
          headers: {
            "content-type": "application/json",
            "x-access-token": token_val
          },
          data: JSON.stringify(child_ajaxData),
          dataType: "json",
          type: "POST"
        }).done(function (data, textStatus, jqXHR) {
          delete d.fetching;
          d.fetched = true;
          d.last_time = data.data.last_time;
          if (data && data.data.child_data.length > 0)
            hideParentChild(d, data.data.child_data);
        }) .fail(function (jqXHR, exception) {
          delete d.fetching;
        })
      }
    } else {
      if (d.data.action === 'PROC_CREATE' && d.node_type!='root') {
        var url = window.location.pathname;

        token_value = localStorage.getItem('token');
        let url_get_events_by_pgid = environment.api_url + '/alerts/process';
        let ajaxData = {
          "process_guid": d.data.process_guid,
          "node_id":id
        }

        get_events_by_pgid();

        function get_events_by_pgid() {
          $.ajax({
            url: url_get_events_by_pgid,
            contentType: "application/json",
            headers: {
              "content-type": "application/json",
              "x-access-token": token_value
            },
            data: JSON.stringify(ajaxData),
            dataType: "json",
            type: "POST"
          }).done(function (data, textStatus, jqXHR) {

            d.fetched = true;
            delete d.fetching;
            if (data && data.data.all_children.length > 0)
              hideParentChild(d, data.data.all_children);

          })  .fail(function (jqXHR, exception) {
            delete d.fetching;

          })
        }

      }

    }
  }

  function hideParentChild(d, data) {

    d.children = null;
    if (d.all_children) {
      Array.prototype.push.apply(d.all_children, data)

    } else {
      d.all_children = data;

    }
    d._children = d.all_children;
    click(d);
  }


  var coll2 = document.getElementsByClassName("collapsible2");
  var n;

  for (n = 0; n < coll2.length; n++) {
    coll2[n].addEventListener("click", function () {
      this.classList.toggle("active_1");
    });
  }

  function selectedNode(info) {
    let el = info.data;
    var eventsData_process = document.getElementById('eventsData_process');
    // if (eventsData_process) {
    while (eventsData_process.firstChild) eventsData_process.removeChild(eventsData_process.firstChild);
    // }


    if (el) {

      // delete el.utc_time;
      // delete el.time;
      // delete el.process_guid;

      // for (let i=0; i < el.events.length; i++){

      var TableRow = '';
      var title=el.eid;
      if(title==undefined){
        title=el.process_guid;
      }
      TableRow +=
        '<div class="card" style="margin-bottom: 0.2rem;">' + '<div class="card-header" id="label_2' + title + '">' +
        '<h5 class="mb-0" style="">' + '<button class="btn" data-toggle="collapse"  aria-expanded="false">'
        + title
        + '</button>'
        + '</h5>'
        + '</div>'
        + '<div class="collapse show">'
        + '<div class="card-body">'
        + '<div id ="' + el.action + 'column_data">'
        + '</div>'
        + '</div>'
        + '</div>'
        + '</div>';
      TableRow += '';

      $('#eventsData_process').append(TableRow);
      var tbl = document.createElement("table");
      tbl.setAttribute("class", "table table-striped- table-bordered table-hover table-checkable");
      tbl.setAttribute("style", "margin-bottom: 0rem;");
      for (let child in el) {
        var row = document.createElement("tr");
        var cell1 = document.createElement("td");
        var cell2 = document.createElement("td");
        var firstCellText = document.createTextNode(child);
        var secondCellText = document.createTextNode(el[child]);
        cell1.appendChild(firstCellText);
        cell1.style.fontSize = "11px";
        cell1.style.fontWeight = '600';
        // cell1.style.fontFamily = "Roboto";
        // cell1.style.color = '#212529';
        cell1.style.wordBreak = "break-all";
        cell1.style.minWidth = "75px"
        cell1.appendChild(secondCellText);
        cell2.style.fontSize = "10px";
        cell2.style.fontWeight = '500';
        // cell2.style.fontFamily = "Roboto";
        // cell2.style.color = '#212529';
        cell2.style.wordBreak = "break-all";
        var data = el[child];
        var is_hyperlink = false;
        var domain_md5_link;
        if (child === 'domain_name') {
          domain_md5_link = "https://www.virustotal.com/#/domain/" + data.substring(1, data.length);
          is_hyperlink = true;
        } else if (child == 'md5') {
          domain_md5_link = "https://www.virustotal.com/#/file/" + data + "/detection";
          is_hyperlink = true;


        }
        if (is_hyperlink == true) {
          var atag = document.createElement("a");
          atag.target = "_blank";
          atag.style.color = "blue";
          atag.href = domain_md5_link;
          atag.appendChild(secondCellText);
          cell2.appendChild(atag);

        } else {
          cell2.appendChild(secondCellText);

        }

        // cell2.setAttribute("class", "cellCss");

        row.appendChild(cell1);
        row.appendChild(cell2);
        tbl.appendChild(row);
      }
      var column_data = document.getElementById(el.action + 'column_data');
      if (column_data) {
        column_data.appendChild(tbl);
      }

    } else {
      var TableRow = '';
      TableRow += '<h5 class="mb-0" style="text-align: center;font-size: 12px; color: #788093; margin-right: 65px; margin-top: 35px;">' + 'Click an event node to view information'
        + '</h5>'

      TableRow += '';
      $('#eventsData_process').append(TableRow);
      var tbl = document.createElement("table");
    }
  }

  selectedNode('info');
}
process_guid_graph(eventdata,process_guid){
  var $: any;
  this.initialise_val(eventdata,process_guid);
  this.openModal('processTree')
  // $('#processTree').modal('show');

}
close_data(){
  document.getElementById("d3-graph-2").innerHTML = '';
}

//Delete Host
deleteHost(host_name){
  swal({
    title: 'Are you sure?',
    text: "Want to delete the host "+ host_name,
    content: {
      element: "span",
      attributes: {
         innerHTML: "Note :Please make sure that you have uninstalled the agent on the host",
      },
    },
    icon: 'warning',
    buttons: ["Cancel", true],
    closeOnClickOutside: false,
    dangerMode: true,
    }).then((willDelete) => {
    if (willDelete) {
      this.commonapi.delete_host(this.id).subscribe(res =>{
        console.log(res);
        swal({
      icon: 'success',
      title: 'Deleted!',
      text: 'Host has been deleted.',
      buttons: [false],
      timer: 2000
      })
    })
    this.router.navigate(['/hosts']);
  }
})
}
disableHost(){
  swal({
    title: 'Are you sure?',
    text: "You want to Remove Host!",
    icon: 'warning',
    buttons: ["Cancel", "Yes, Remove it!"],
    dangerMode: true,
    closeOnClickOutside: false,
    }).then((willDelete) => {
    if (willDelete) {
      this.commonapi.DisableHost(this.host_identifier).subscribe(res => {
    swal({
    icon: 'success',
    text: 'Successfully Removed the host',
    buttons: [false],
    timer:1500
    })
    })
    this.router.navigate(['/hosts']);
    }
    })
}
ngOnChanges() {
  if(this.refreshStatus){
    clearInterval(this.refreshStatus)
  }
  if(this.initialised){
    // if(this.nodes?.platform == 'windows'){
    //   this.resetDefenderInputs()
    // }
    this.showLoader = true;
    // this.GetQuarantineDiv = false;
    this.log_data = [];
    if(this.hostData?.state == 1 || this.hostState == 1){
      this.isDisabled = true
    }
    else{
      this.isDisabled = false
    }
    this.status_log_tab();
    this.sub = this._Activatedroute.paramMap.subscribe(params => {
      if (this.hostData != undefined || this.hostData != null) {
        this.id = this.hostData.id;
      }
      else {
        this.id = params.get('id');
      }
    this.commonapi.host_name_api(this.id).subscribe(res => {
      this.activitydata = res;
      if(this.activitydata.status == "failure"){
        this.pagenotfound();
      }
      else{
      this.newPlatform = this.activitydata.data?.platform
      this.host_identifier = this.activitydata.data.host_identifier


      //Changing tabs if security center was selected but new host is not windows
      if(this.isSecurityCenterActive && this.newPlatform != 'windows'){
        this.isSecurityCenterActive = false;
        $('.nav-tabs.node-tabs li:first-child a').tab('show');
      }
      // this.nodekey = this.activitydata.data.node_key;
      if (this.activitydata.data.id == this.id) {
        this.nodes = this.activitydata.data
      }
    }
    });

    this.fetchData()
    this.refreshStatus = setInterval(()=>{
      this.fetchData()
    }, 30000);
    let additional_config =this.commonapi.additional_config_api(this.id).subscribe(res =>{
        this.additionaldata=res;
        if(this.additionaldata != undefined){
          this.packs_count = Object.keys( this.additionaldata.data.packs ).length;
        this.pack_name = this.additionaldata.data.packs;
        this.query_names = this.additionaldata.data.queries;
        this.query_count = Object.keys( this.additionaldata.data.queries ).length;
        this.tags = this.additionaldata.data.tags;
        this.searchText;
        if(this.additionaldata.data.packs.length>0){
          this.getfirstpack_data();
        }

        if (this.additionaldata.data.queries.length>0){
          this.getfirst_data();
        }
        }

    })
    // this.Getdefenderlog();




  this.commonapi.recent_activity_count_api(this.id).subscribe(res => {
    this.nodesdata = res;
        if(this.nodesdata.data != undefined && this.nodesdata.data != null && this.nodesdata.data[0] != undefined ){
          this.activitynode = this.nodesdata.data;
          this.selected_query=this.activitynode[0]?.name
          this.query_name=this.activitynode[0]?.name;
          if(this.query_name == undefined || this.query_name == null){
            this.query_name = ''
          }
          this.query_name = Array(this.query_name)
          this.activitycount = Object.keys(this.activitynode).length;

          this.searchText;

          this.defaultData=true;
          this.getFromActivityData();
          this.Refresh_datatable()
          this.isRecentActivityEmpty = false
        }
        else{
          this.isRecentActivityEmpty = true
        }
        this.showLoader = false;
      }, err =>{
        this.showLoader = false;
      });

      this.Host_Alerted_rules();
    })
  }
}


private tagValidation(control: FormControl) {
  var maxTagInput = (environment?.max_tag_size)? environment.max_tag_size : 64;
    if (control.value.length > maxTagInput ) {
      return {
          'errorMsg': true
      };
  }

  return null;
}
public validators = [this.tagValidation];
public errorMessages = {
  'errorMsg': 'Tag should not be more than ' + this.maxTagCharacters + ' characters'
};
omitSpecialChar(event){
   return this.tagsValidation.omitSpecialChar(event)
}

searchPack(searchTerm){
   var arrayPackDictionary = [];
   this.packsCategoryDictionary = this.tempPacksCategoryDictionary;
   this.packsCategoryDictionary.forEach(function (packitem) {
     var filterpackDictionary = packitem.packs.filter(n => n.includes(searchTerm));
     if(filterpackDictionary.length > 0){
       arrayPackDictionary.push({'category':packitem.category,'packs':filterpackDictionary})
      }
    });
    this.packsCategoryDictionary = arrayPackDictionary;
 }

 validatePastedData(event){
  console.log('event')
  if(!this.tagsValidation.validatePastedData(event)){
    this.toastr.error('Accepts only alpha numeric characters with @._\-','',{ timeOut: 1000});
  }
}

}
