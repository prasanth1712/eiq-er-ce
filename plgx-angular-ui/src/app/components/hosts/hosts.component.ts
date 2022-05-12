import { Component, OnInit,ViewChild } from '@angular/core';
import { CommonapiService } from '../../dashboard/_services/commonapi.service';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import swal from 'sweetalert';
import { environment } from '../../../environments/environment';
import 'datatables.net';
import { DataTableDirective } from 'angular-datatables';
import { Subject } from 'rxjs';
import { AuthorizationService } from '../../dashboard/_services/Authorization.service';
import { FormGroup, FormBuilder, Validators, FormControl } from '@angular/forms';
  class DataTablesResponse {
    data: any[];
    draw: number;
    recordsFiltered: number;
    recordsTotal: number;
  }
  @Component({
    selector: 'app-hosts',
    templateUrl: './hosts.component.html',
    styleUrls: ['./hosts.component.scss']
  })
  export class HostsComponent implements OnInit {
    windows_online:any;
    windows_offline:any;
    ubuntu_online:any;
    ubuntu_offline:any;
    darwins_online:any;
    darwins_offline:any;
    count_all:any;
    hosts_status:any;
    hosts_platform:any;
    hostmainvalue_data:any;
    token_value:any;
    dtOptions: DataTables.Settings = {};
    @ViewChild(DataTableDirective, {static: false})
    dtElement: DataTableDirective;
  dtTrigger: Subject<any> = new Subject();
    errorMessage:any;
    role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess}
    constructor(
        private commonapi: CommonapiService,
        private http: HttpClient,
        private authorizationService: AuthorizationService,
        private fb: FormBuilder,
    ) { }

    ngOnInit() {

      this.get_hosts_count()
      this.dtOptions = {
        pagingType: 'full_numbers',
        pageLength: 25,
        serverSide: true,
        processing: true,
        searching: true,
        scrollCollapse: true,
        // scrollX: true,
        // "scrollY": '400px',
        "initComplete": function (settings, json) {
          $("#host_table").wrap("<div style='overflow:auto; width:100%;position:relative;max-height:480px'></div>");
         },
        "language": {
          "search": "Search: "
        },
        ajax: (dataTablesParameters: any,callback) => {
          this.get_hosts_count()
          var body = dataTablesParameters;
          body['limit']=body['length'];
          if(this.hosts_platform!='' && this.hosts_platform!='all'){
          body['status']=this.hosts_status
          body['platform']=this.hosts_platform
        }
          if(body.search.value!= ""  &&  body.search.value.length>=1)
        {
          body['searchterm']=body.search.value;
        }
        if(body['searchterm']==undefined){
              body['searchterm']="";
            }

          this.http.post<DataTablesResponse>(environment.api_url+"/hosts", body,{ headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res =>{
            localStorage.removeItem('nodeid');
            this.hostmainvalue_data = res.data['results'];
          if(this.hostmainvalue_data.length >0 &&  this.hostmainvalue_data!=undefined){
            this.hostmainvalue_data = res.data['results'];
            this.hostmainvalue_data.sort((x,y) => y.is_active - x.is_active)
            $('.dataTables_paginate').show();
            $('.dataTables_info').show();
          }else{
            if(body.search.value=="" || body.search.value == undefined){
              this.errorMessage = "No Host Found";
              $('.dataTables_paginate').hide();
              $('.dataTables_info').hide();
            }
            else{
              this.errorMessage = "No Matching Record Found";
              $('.dataTables_paginate').hide();
              $('.dataTables_info').hide();
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
        columns: [{ data: 'display_name' },{data:'online'},{data:'health'},{ data: 'os_info' }, { data: 'last_ip' }, { data: 'tags' },{ data: 'delete' }]
      }

      this.token_value = localStorage.getItem('token');
      $(document).ready(() => {
          var TableRow = '';
              TableRow += '<button type="button" value =this.token_value href="javascript:void(0);" id ="export_option" class="btn btn-outline-success btn-sm btn-icon-sm" title="Download CSV File" alt="" value="" >' + '<i class="la la-download"></i>' + 'Export'
                  + '</button>'

              TableRow += '';
              $('#exportData').append(TableRow);
          var token_val = this.token_value;
              $("#export_option").on('click', function(event){
              var currentDate = new Date();

              $.ajax({
                  "url": environment.api_url+"/hosts/export",
                  "type": 'GET',
                  headers: {
                      "content-type":"application/json",
                      "x-access-token": token_val
                    },
                  "success": function(res, status, xhr) {
                      var csvData = new Blob([res], {
                          type: 'text/csv;charset=utf-8;'
                      });
                      var csvURL = window.URL.createObjectURL(csvData);
                      var tempLink = document.createElement('a');
                      tempLink.href = csvURL;
                      tempLink.setAttribute('download', 'nodes' + '_' + currentDate.getTime() + '.csv');
                      document.getElementById('container').appendChild(tempLink);
                      tempLink.click();
                  }
              });
              return false;
          });
      });
    }
    value : any;

    private startsWithAt(control: FormControl) {
      if (control.value.length > 50 ) {
          return {
              'startsWithAt@': true
          };
      }

      return null;
  }
  public validators = [this.startsWithAt];
  public errorMessages = {
    'startsWithAt@': 'Tag should not be more then 50 characters'
};

    get_hosts_count(){
      this.commonapi.Hosts_count().subscribe((res:any) => {
        this.windows_online = res.data.windows.online;
        this.windows_offline = res.data.windows.offline;
        if(this.windows_online !=='' || this.windows_online !==''){
          $('.window_widget_body').show();
        $('.window_widget_body2').hide();
        }
        this.ubuntu_online = res.data.linux.online;
        this.ubuntu_offline = res.data.linux.offline;
        if(this.ubuntu_online !=='' || this.ubuntu_offline !==''){
          $('.linux_widget_body').show();
        $('.linux_widget_body2').hide();
        }
        this.darwins_online = res.data.darwin.online;
        this.darwins_offline = res.data.darwin.offline;
        if(this.darwins_online !=='' || this.darwins_offline !==''){
          $('.apple_widget_body').show();
        $('.apple_widget_body2').hide();
        }
        this.count_all=this.windows_online+this.windows_offline+this.ubuntu_online +this.ubuntu_offline+this.darwins_online +this.darwins_offline;
    });
    }
    disableHost(host_id){
      swal({
        title: 'Are you sure?',
        text: "You want to Remove Host!",
        icon: 'warning',
        buttons: ["Cancel", "Yes, Remove it!"],
        dangerMode: true,
        closeOnClickOutside: false,
        }).then((willDelete) => {
        if (willDelete) {
          this.commonapi.DisableHost(host_id).subscribe(res => {
        swal({
        icon: 'success',
        text: 'Successfully Removed the host',
        buttons: [false],
        timer:1500
        })
        setTimeout(() => {
          this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
            dtInstance.destroy();
            this.dtTrigger.next();
          });
          },500);
        })

        }
        })
    }
    ngAfterViewInit(): void {
      this.dtTrigger.next();
    }

    ngOnDestroy(): void {
      this.dtTrigger.unsubscribe();
    }
    getByFilterId(status, platform){
      if(platform!="all"){
      this.hosts_status=status
      this.hosts_platform=platform
      this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
        dtInstance.destroy();
        this.dtTrigger.next();
      });
    }
      if(platform=="all"){
        this.hosts_status='',
        this.hosts_platform='',
            this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
              dtInstance.destroy();
              this.dtTrigger.next();
            });
      }
     }
    hosts_addTag(tags,node_id){
      this.commonapi.hosts_addtag_api(node_id,tags.toString()).subscribe(res => {
      });
    }
    hosts_removeTag(event,node_id) {
      this.commonapi.hosts_removetags_api(node_id,event).subscribe(res => {
      });
    }
  }
