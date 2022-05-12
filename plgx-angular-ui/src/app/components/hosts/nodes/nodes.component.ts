import { AfterViewInit, Component, OnDestroy, OnInit, ViewChild,ElementRef } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../../dashboard/_services/commonvariable.service';
import { ActivityComponent } from '../../../components/hosts/activity/activity.component';
import { environment } from '../../../../environments/environment';
import * as $ from 'jquery';
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
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import Swal from 'sweetalert2';
import { AuthorizationService } from '../../../dashboard/_services/Authorization.service';
import { compare } from 'compare-versions';
import { moment } from 'vis-timeline';
let currentQueryID;
let gotResultsFromSocket;
var PaginationIndex
var TempIndex
var NextDataId
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

export class NodesComponent implements AfterViewInit, OnInit, OnDestroy {
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
  interval :any;
  dataRefresher: any;
  responce_action:Subscription;
  alerted_data_json:any;
  additional_config_data:any;
  status_log_checkbox=false;
  selectedItem:any;
  actionselect:any=0;
  host_identifier:any;
  os_platform:any;
  os_name:any;
  alertlist:any;
  alienvault = <any>{};
  ibmxforce = <any>{};
  rule = <any>{};
  virustotal = <any>{};
  windows_defender_status:any;
  windows_defender_list = [];
  keys:any;
  defenderstatus = true;
  project_name=this.commonvariable.APP_NAME;
  osInfo:any;
  startedAt: any;
Malware_Events_dropdownList = []
Malware_Events_selectedItems = [];
Malware_Events_dropdownSettings = {};
scriptform: FormGroup;
file_content:File;
file_name:any;
script_type_name=''
script_type_value=''
  public temp_var: Object=false;
    hosts_addtags_val:any;
    hosts_removetags_val:any;
    pack_addtags_val:any;
    pack_removetags_val:any;
    queries_addtags_val:any;
    queries_removetags_val:any;
  dtOptions: any = {};
  DefenderdtOptions: any = {};
  testdtOptions: DataTables.Settings = {};
  dtTrigger: Subject<any> = new Subject();
  @ViewChild(DataTableDirective, {static: false})
  dtElement: DataTableDirective;
  PreviousDataIds={}
  istabopen:boolean=false;
  list_of_QuarantineThreats=[]
  config_list_dropdownList = [];
  config_list_selectedItems = [];
  config_list_dropdownSettings = {}
  public submit_button_disable_enable: boolean = false;
  role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess};
  compareAgentVersion:boolean;
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
  ) { }
  toggle:boolean=false;

  ngOnInit() {
    // $("#Quarantine_Threats_no_data").hide();
    // $('.quarantine_loader').hide();
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Hosts" );
    this.sub = this._Activatedroute.paramMap.subscribe(params => {
        this.id = params.get('id');
    localStorage.setItem('hostid', this.id);
    this.fetchData()
    let additional_config =this.commonapi.additional_config_api(this.id).subscribe(res =>{
        this.additionaldata=res;
        this.packs_count = Object.keys( this.additionaldata.data.packs ).length;
        this.pack_name = this.additionaldata.data.packs;
        this.query_count = Object.keys( this.additionaldata.data.queries ).length;
        this.query_name = this.additionaldata.data.queries;
        this.tags = this.additionaldata.data.tags;
        this.searchText;
        if(this.additionaldata.data.packs.length>0){
          this.getfirstpack_data();
        }

        if (this.additionaldata.data.queries.length>0){
          this.getfirst_data();
        }

    })
    this.interval = setInterval(() => {
      this.refreshData();
    }, 10000);
    // this.Getdefenderlog();
    })
    this.Host_Alerted_rules();
    this.scriptform = this.fb.group({
      script_type:'',
      save_script:'',
      params:'',
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
        text:"Select Malware Events",
        selectAllText:'Select All',
        unSelectAllText:'UnSelect All',
        enableSearchFilter: true,
        classes:"myclass custom-class"
      };
      this.Malware_Events_dropdownList = [
      { 'id': "1006,1116", 'itemName': "Malware found" },
      { 'id': "1007", 'itemName': "Malware action taken" },
      { 'id': "1008", 'itemName': "Malware action failed" },
      // { 'id': "2000,2002", 'itemName': "Malware definitions updated" },
      // ​{ 'id': "2001,2003", 'itemName': "Malware definitions update failed" },
      ​{ 'id': "1000", 'itemName': "Malwareprotection scan started" },
      { 'id': "1001", 'itemName': "Malwareprotection scan completed" },
      { 'id': "1002", 'itemName': "Malwareprotection scan cancelled" },
      ​ { 'id': "1003", 'itemName': "Malwareprotection scan paused" },
      ​{ 'id': "1004", 'itemName': "Malwareprotection scan resumed" },
      { 'id': "1005", 'itemName': "Malwareprotection scan failed" },
      // { 'id': "1006", 'itemName': "Malwareprotection malware detected" },
      // { 'id': "1007", 'itemName': "Malwareprotection malware action taken" },
      // ​{ 'id': "1008", 'itemName': "Malwareprotection malware action failed" },
      { 'id': "1009", 'itemName': "Malwareprotection quarantine restore" },
      ​{ 'id': "1010", 'itemName': "Malwareprotection quarantine restore failed" },
      { 'id': "1011", 'itemName': "Malwareprotection quarantine delete" },
      ​{ 'id': "1012", 'itemName': "Malwareprotection quarantine delete failed" },
      { 'id': "1013", 'itemName': "Malwareprotection malware history delete" },
      ​{ 'id': "1014", 'itemName': "Malwareprotection malware history delete failed" },
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
      ​{ 'id': "2004", 'itemName': "Malwareprotection signature reversion" },
      ​{ 'id': "2005", 'itemName': "Malwareprotection engine update platformoutofdate" },
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
      ​{ 'id': "5000", 'itemName': "Malwareprotection rtp enabled" },
      ​{ 'id': "5001", 'itemName': "Malwareprotection rtp disabled" },
      { 'id': "5004", 'itemName': "Malwareprotection rtp feature configured" },
      { 'id': "5007", 'itemName': "Malwareprotection config changed" },
      { 'id': "5008", 'itemName': "Malwareprotection engine failure" },
      ​{ 'id': "5009", 'itemName': "Malwareprotection antispyware enabled" },
      { 'id': "5010", 'itemName': "Malwareprotection antispyware disabled" },
      { 'id': "5011", 'itemName': "Malwareprotection antivirus enabled" },
      ​{ 'id': "5012", 'itemName': "Malwareprotection antivirus disabled" },
      { 'id': "5100", 'itemName': "Malwareprotection expiration warning state" },
      { 'id': "5101", 'itemName': "Malwareprotection disabled expired state" },
      ];
    }
    get s() { return this.scriptform.controls; }
    private async fetchData(){
      const data = await this.commonapi.host_name_api(this.id).toPromise();
      this.data = data;
      if(this.data.status == "failure"){
        this.pagenotfound();
      }
      else{
        if(this.data.data.id == this.id){
            this.nodes = this.data.data;
            console.log(this.nodes);
            this.node_id = this.nodes.id;
            this.network_info = this.nodes.network_info;
            this.host_identifier = this.nodes.host_identifier
            if(this.nodes.os_info != null){
            this.osInfo = this.nodes.os_info;
            this.os_platform = this.nodes.os_info.platform;
            this.os_name = this.nodes.os_info.name;
            }
            this.hostDetails = this.nodes.host_details;
            if(this.hostDetails['extension_version']){
              console.log(this.compareAgentVersion)
              this.compareAgentVersion=compare(this.hostDetails['extension_version'], "3.0", '<')
            }
            if(this.nodes.platform=='windows' && !this.hostDetails.hasOwnProperty('windows_security_products_status')){
              this.hideDefender(msg.unableFetchMsg);
            }
            //Security Center is supported only on Windows 8 and above
            if(this.os_name.includes("Windows 7") || this.os_name.includes("Windows Server") ){
              this.hideDefender(msg.windowsErrorMsg);
            }
            this.windows_defender_status = this.hostDetails.windows_security_products_status;
            this.node_info = this.nodes.node_info;
            this.physical_memory = this.physical_memory_formate(this.nodes.node_info.physical_memory);
            this.currentdate = new Date();

            if(!this.hostDetails){
              this.hostDetails={};
            }

            if(!this.hostDetails['osquery_version']){
              this.hostDetails['osquery_version'] = "-";
            }

            if(!this.hostDetails['extension_version']){
              this.hostDetails['extension_version'] = "-";
            }
            if(this.nodes.last_checkin==null){
              this.lastcheckin=''

            }else{
              var lastCheckinUtc = moment.utc(this.nodes.last_checkin).format();
              this.lastcheckin = moment(lastCheckinUtc).fromNow();

            }


            if(this.nodes.enrolled_on==null){
              this.enrolled=''
            }else{
              this.enrolled = new Date(this.nodes.enrolled_on);
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
              var lastResultutc = moment.utc(this.nodes.last_result).format();
              this.lastresult = moment(lastResultutc).fromNow();
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
              var lastQueryWriteutc = moment.utc(this.nodes.last_query_write).format();
              this.lastquerywrite = moment(lastQueryWriteutc).fromNow();
            }
        }
        if(this.nodes.platform=='windows'){
          this.script_type_value='2'
          this.script_type_name='PowerShell Script'
        }else{
          this.script_type_value='4'
          this.script_type_name='Shell Script'
        }
      }
    }

    hideDefender(msg){
      $('.show_Manage_Defender').hide()
      $(".show_NotApplicable_Msg").html(msg);
    }

    Host_Alerted_rules(){
     let host_id = localStorage.getItem('hostid');
     let alertedrules=this.commonapi.Host_rules_api(host_id).subscribe(res => {
      this.alertlist = res;
      if(this.alertlist.status == "success"){
        this.alienvault = this.alertlist.data.sources.alienvault;
        this.ibmxforce = this.alertlist.data.sources.ibmxforce;
        this.rule = this.alertlist.data.sources.rule;
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
          $(document.getElementById('no-data-bar-chart-top_5_alerted_rules')).append("No Rule Based Alerts");
       }else{
        this.load_top_rules_graph(rule_name,rule_count)
       }
      }

    });
    }

    load_top_rules_graph(rule_name,rule_count){
      var myChartsdaklns = new Chart('alerted_rules', {
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
            responsive: false,
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

         //ctx.myChartsdaklns = 230;
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
      this.toggle=false;
      setTimeout(()=>{
        this.editorOptions = new JsonEditorOptions();
        this.editorOptions.mode = 'view';
        this.alerted_data_json=res['data'];
        this.toggle=true;
      }, 100);
    })
      this.config_list_dropdownList=[]
      this.commonapi.configs_api().subscribe((res: any) => {
        if(!['windows','darwin'].includes(this.nodes['platform'])){
          this.nodes['platform'] = 'linux'
        }
      for (const i in res.data[this.nodes['platform']]){
        this.config_list_dropdownList.push({id: res['data'][this.nodes['platform']][i]['id'], itemName: i});
      }
      })
    }
    Assign_config(){
      var payload = {"host_identifiers":this.host_identifier}
      if(this.config_list_selectedItems.length>0){
      this.commonapi.asign_config_to_hosts(this.config_list_selectedItems[0]['id'],payload).subscribe(res=>{
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
                this.enrolled = new Date(this.nodes.enrolled_on);
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

        // this.getData(false);
        //Passing the false flag would prevent page reset to 1 and hinder user interaction

    }
    ngOnDestroy() {
        clearInterval(this.interval)
        window.clearInterval(this.interval);
        // clearInterval(this.defenderTimeout)
        clearTimeout(set_time_out)
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
    this.dtTrigger.next();
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
    this.router.navigate(['live-queries/', queryId]);
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
    this.dtOptions = {
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
            that.exportstatuslog();
          },
        },
      ],
      "language": {
        "search": "Search: "
      },
      ajax: (dataTablesParameters: any, callback) => {
        var body = dataTablesParameters;
        body['limit']=body['length'];
        if(body.search.value!= ""){
          body['searchterm']=body.search.value;
        }
        let host_id = localStorage.getItem('hostid');
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
              this.errorMessage="No Data Found";
              var Export_Element = document.getElementById("IdExport");
              Export_Element.classList.add("disabled");
            }
            else{
              this.errorMessage="No Matching Record Found";
            }

            $('.dataTables_paginate').hide();
            $('.dataTables_info').hide();

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
    let host_id = localStorage.getItem('hostid');
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

  Refresh_datatable(){
    this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
      dtInstance.destroy();
      this.dtTrigger.next();
    });
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
uploadFile(event){
  if (event.target.files.length > 0) {
      this.file_content = event.target.files;
      this.file_name = this.file_content[0].name;
  }
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
onItemSelect_config(item: any) {
  console.log(item);
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
}
