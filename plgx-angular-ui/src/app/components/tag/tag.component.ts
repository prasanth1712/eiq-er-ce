

import { AfterViewInit, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';import { CommonapiService } from '../../dashboard/_services/commonapi.service';
import { FormGroup, FormBuilder, FormArray, Validators, FormControl } from '@angular/forms';
import swal from 'sweetalert';
// import * as $ from 'jquery';
import 'datatables.net';
import { DataTableDirective } from 'angular-datatables';
import { Subject } from 'rxjs';

import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';
import { linkVertical } from 'd3';
import { AuthorizationService } from '../../dashboard/_services/Authorization.service';

class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}
class tags_data {
  value: string;
  packs: string;
  queries: string;
  nodes: string;
}
@Component({
  selector: 'app-tag',
  templateUrl: './tag.component.html',
  styleUrls: ['./tag.component.css']
})
export class TagComponent implements AfterViewInit, OnInit {
  @ViewChild(DataTableDirective, {static: false})
  dtElement: DataTableDirective;
  dtTrigger: Subject<any> = new Subject();
  tags_val:any;
  tags_data:any;
  addTag: FormGroup;
  add_tags_val:any;
  delete_tags_val:any;
  submitted = false;
  addTagobj=[];
  temp_var:any;
  tags:any;
  dtOptions: DataTables.Settings = {};
  searchText:string;
  errorMessage:any;
  role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess}
  constructor(
    private commonapi:CommonapiService,
    private fb:FormBuilder,
    private router: Router,
    private http: HttpClient,
    private authorizationService: AuthorizationService,
  ) { }

  ngOnInit() {
    this.addTag= this.fb.group({
      tags:''
    });
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
        body['limit']=body['length'];
        if(body.search.value!= ""  &&  body.search.value.length>=1)
      {

        body['searchterm']=body.search.value;

      }


        if(body['searchterm']==undefined){
          body['searchterm']="";
        }

        this.http.get<DataTablesResponse>(environment.api_url+"/tags"+"?searchterm="+body['searchterm']+"&start="+body['start']+"&limit="+body['limit'],{ headers: {'x-access-token': localStorage.getItem('token')}}).subscribe(res =>{

          this.tags_val = res ;
        this.tags_data = this.tags_val.data.results;
          this.temp_var=true;
        if(this.tags_data.length >0 &&  this.tags_data!=undefined)
        {
        this.tags_data = this.tags_val.data['results'];
          // $("#DataTables_Table_0_info").
          $('.dataTables_paginate').show();
          $('.dataTables_info').show();
          $('.dataTables_filter').show()
        }
        else{
          if(body.search.value=="" || body.search.value == undefined)
          {
            this.errorMessage="No tags created. You may create new tags";
          }
          else{
            this.errorMessage="No Matching Record Found";
          }

          $('.dataTables_paginate').hide();
          $('.dataTables_info').hide();

        }
          callback({
            recordsTotal: this.tags_val.data.total_count,
            recordsFiltered: this.tags_val.data.count,
            data: []
          });
        });
      },
      ordering: false,
      columns: [{ data: 'value' }, { data: 'packs' }, { data: 'queries' }, { data: 'nodes' }]
    }

  }

  get f() { return this.addTag.controls; }

  clearValue:string = '';
  clearInput() {
    this.clearValue = null;
  }

  Cancel(){
    this.clearValue = '';
  }

  onSubmit(){
    this.submitted = true;
    if (this.addTag.invalid) {
              return;
    }
    let tags = this.addTag.value.tags
    if(tags == ''){
      swal({
        icon: 'warning',
        text: 'Please Enter Tag',

      })
    }else{
      let tags_list = (tags.split('\n')).filter(x => x !== '');
    for(const i in tags_list){
    this.commonapi.add_tags_api(tags_list[i].trim()).subscribe(res => {
      this.add_tags_val = res ;
      if(this.add_tags_val && this.add_tags_val.status === 'failure'){
        swal({
          icon: 'warning',
          title: this.add_tags_val.status,
          text: this.add_tags_val.message,

        })
        this.clearInput()

      }else if(this.add_tags_val && this.add_tags_val.status === 'success'){
        swal({
          icon: 'success',
          title: this.add_tags_val.status,
          text: this.add_tags_val.message,
          buttons: [false],
          timer: 2000
        })
    //     setTimeout(() => {
    //       this.clearInput()
    //       this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
    //         // Destroy the table first
    //         dtInstance.destroy();
    //         // Call the dtTrigger to rerender again
    //         this.dtTrigger.next();
    //       });
    // },1500);
      }
    });
  }
  setTimeout(() => {
    this.clearInput()
    this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
      dtInstance.destroy();
      this.dtTrigger.next();
    });
},1500);
}

  }
  ngAfterViewInit(): void {
    this.dtTrigger.next();
  }
  deleteTag(event){
  var tags_val = event.target.value;
  // console.log("ht",tags_val);
    swal({
    title: 'Are you sure?',
    text: "You won't be able to revert this!",
    icon: 'warning',
    buttons: ["Cancel", true],
    closeOnClickOutside: false,
    dangerMode: true,
    }).then((willDelete) => {
    if (willDelete) {
    this.commonapi.delete_tags_api(tags_val).subscribe(res=>{
    this.delete_tags_val = res;
      swal({
      icon: 'success',
      title: 'Deleted!',
      text: 'Tag has been deleted.',
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
