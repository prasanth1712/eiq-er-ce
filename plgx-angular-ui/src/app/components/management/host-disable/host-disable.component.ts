import { Component, OnDestroy,OnInit,ViewChild,AfterViewInit } from '@angular/core';
import { Title } from '@angular/platform-browser';
import 'datatables.net';
import { Subject } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { HttpClient, HttpResponse } from '@angular/common/http';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../../dashboard/_services/commonvariable.service';
import { Location } from '@angular/common';
import { DataTableDirective } from 'angular-datatables';
import swal from 'sweetalert';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthorizationService } from '../../../dashboard/_services/Authorization.service';
class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}
class hostmainvalue_data {
  display_name: string;
  os_info: string;
  last_ip: string;
  tags: string;
  delete: string;

}

@Component({
  selector: 'app-host-disable',
  templateUrl: './host-disable.component.html',
  styleUrls: ['./host-disable.component.css','./host-disable.component.scss']
})
export class HostDisableComponent implements AfterViewInit, OnInit {
  @ViewChild(DataTableDirective, {static: false})
  dtElement: DataTableDirective;
  dtOptions: any = {};
  dtTrigger: Subject<any> = new Subject();
  response_data: any;
  customresults: any[] = [];
  results: any;
  errorMessage:any;
  hostmainvalue_data:any;
  hosts_addtags_val:any;
    hosts_removetags_val:any;
    temp_var:any;
    hosts_enable:any;
    role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess}
  constructor(
    private titleService: Title,
    private commonapi: CommonapiService,
    private commonvariable: CommonVariableService,
    private http: HttpClient,
    private _location: Location,
    private _router: Router,
    private authorizationService: AuthorizationService,

  ) { }

  ngOnInit() {
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Removed hosts");

    this.dtOptions = {
      pagingType: 'full_numbers',
      pageLength: 10,
      serverSide: true,
      processing: false,
      searching: true,
      "language": {
        "search": "Search: "
      },
      ajax: (dataTablesParameters: any,callback) => {

        var body = dataTablesParameters;
        console.log(body)
        body['enabled']="false";
        body['limit']=body['length'];
        if(body.search.value!= ""  &&  body.search.value.length>=1)
      {

        body['searchterm']=body.search.value;

      }

        if(body['searchterm']==undefined){
          body['searchterm']="";
        }

        // this.http.get<DataTablesResponse>(environment.api_url+"/hosts/list"+"?searchterm="+body['searchterm']+"&start="+body['start']+"&limit="+body['limit'],{ headers: {'x-access-token': localStorage.getItem('JWTkey')}}).subscribe(res =>{
          this.http.post<DataTablesResponse>(environment.api_url+"/hosts", body,{ headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res =>{
          this.response_data = res ;
        this.hostmainvalue_data = this.response_data.data.results;
          this.temp_var=true;
        if(this.hostmainvalue_data.length >0 &&  this.hostmainvalue_data!=undefined)
        {
        // this.hostmainvalue_data = this.tags_val.data['results'];
          // $("#DataTables_Table_0_info").
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
            recordsTotal: this.response_data.data.total_count,
            recordsFiltered: this.response_data.data.count,
            data: []
          });
        });
      },
      ordering: false,
      columns: [{ data: 'display_name' }, { data: 'os_info' }, { data: 'last_ip' }, { data: 'tags' },{ data: 'delete' }]
    }
    // this.http.get(environment.api_url+"/hosts/list",{ headers: {'x-access-token': localStorage.getItem('JWTkey')}}).subscribe(res => {
    //     this.response_data = res;
    //     this.hostmainvalue_data = this.response_data.data;
    //     console.log(this.response_data);
    //     // Calling the DT trigger to manually render the table
    //     this.dtTrigger.next();
    //   });
  }
  addNodes(node_id){
    console.log(node_id);
    swal({
      title: 'Are you sure?',
      text: "You want to Restore Host!",
      icon: 'warning',
      buttons: ["Cancel", "Yes, Restore it!"],
      dangerMode: true,
      closeOnClickOutside: false,
      }).then((willDelete) => {
      if (willDelete) {
        this.commonapi.hosts_enablenodes_api(node_id).subscribe(res => {
          this.hosts_enable = res ;
          console.log(res,"res")
         if(this.hosts_enable.status=="failure"){
      swal({
      icon: "warning",
      text: this.hosts_enable.message,
      })
    }else{
      swal({
        icon: "success",
        text: "Successfully Restored the Host",
        buttons: [false],
        timer:1500
        })
      setTimeout(() => {
        this._router.navigate(['./hosts']);
        },500);}
      })
      }
      })

  }
  goBack(){
    this._location.back();
  }
  hosts_addTag(tags,node_id){
    this.commonapi.hosts_addtag_api(node_id,tags.toString()).subscribe(res => {
     this.hosts_addtags_val = res ;
     // swal({
     //   icon: 'success',
     //   title: '',
     //   text: 'Successfully added in Host.',
     // })
     // setTimeout(() => {
     //   location.reload();
     // },2000);
    });
  }
  hosts_removeTag(event,node_id) {
    this.commonapi.hosts_removetags_api(node_id,event).subscribe(res => {
      this.hosts_removetags_val = res ;
    });
  }
  ngAfterViewInit(): void {
    this.dtTrigger.next();
  }
  deleteHost(host_id, host_name){
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
          this.commonapi.delete_host(host_id).subscribe(res =>{
            console.log(res);
            swal({
          icon: 'success',
          title: 'Deleted!',
          text: 'Host has been deleted.',
          buttons: [false],
          timer: 2000
          })
          setTimeout(() => {
            this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
              // Destroy the table first
              dtInstance.destroy();
              // Call the dtTrigger to rerender again
              this.dtTrigger.next();
            });
          },1500);
        })
      }
    })
     }


}
