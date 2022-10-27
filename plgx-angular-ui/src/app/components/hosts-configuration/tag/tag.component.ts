

import { AfterViewInit, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { FormGroup, FormBuilder, FormArray, Validators, FormControl } from '@angular/forms';
import swal from 'sweetalert';
// import * as $ from 'jquery';
import 'datatables.net';
import { DataTableDirective } from 'angular-datatables';
import { Subject } from 'rxjs';
import { TagsValidationHandler } from '../../../dashboard/_helpers/tagsValidationHandler';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { linkVertical } from 'd3';
import { AuthorizationService } from '../../../dashboard/_services/Authorization.service';

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
  @ViewChild(DataTableDirective)
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
  errorMessageTag:any;
  checklist:any=[];
  masterSelected:any;
  searchTerm:any;
  role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess}
  constructor(
    private commonapi:CommonapiService,
    private fb:FormBuilder,
    private router: Router,
    private http: HttpClient,
    private authorizationService: AuthorizationService,
    private tagsValidation:TagsValidationHandler
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
      searching: false,
      "language": {
        "search": "Search: ",
        "info" : "Showing _START_ to _END_ of <b>_TOTAL_</b> entries",
        "lengthMenu": "<ng-container class=custom-pagination-length>Results per page: _MENU_</ng-container>",
      },
      dom: "<'row'<'col-sm-12'f>>" +
      "<'row table-scroll-hidden'<'col-sm-12 mt-18 table-scroll full-height'tr>>" +
      "<'row table-controls custom-pagination-margin'<'col-sm-6 table-controls-li pl-0'li><'col-sm-6 pr-0'p>>",
      ajax: (dataTablesParameters: any,callback) => {
        var body = dataTablesParameters;
        body['limit']=body['length'];
        if(this.searchTerm){
          body['searchterm'] = this.searchTerm
        }
        if(this.searchTerm!= ""  &&  this.searchTerm?.length>=1){
           body['searchterm']=this.searchTerm;
        }
        if(body['searchterm']==undefined){
            body['searchterm']="";
        }
        if (body.order != "" && body.order.length >= 1) {
            body['column']='tags';
            body['order_by']=body['order'][0].dir;
          }
        this.removeSelectedTag();
        this.http.get<DataTablesResponse>(environment.api_url+"/tags"+"?searchterm="+body['searchterm']+"&start="+body['start']+"&limit="+body['limit'],{ headers: {'x-access-token': localStorage.getItem('token')}}).subscribe(res =>{

          this.tags_val = res ;
        this.tags_data = this.tags_val.data.results;
        console.log(this.tags_data);
        this.checklist = [];
        for (const i in this.tags_data) {
          let checkboxdata = {}
          checkboxdata['value'] = this.tags_data[i].value;
          checkboxdata['isSelected'] = false
          this.checklist.push(checkboxdata);
        }
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
    if(this.tagsValidation.isEmpty(tags)){
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
  deleteTag(tagvalue){
    swal({
    title: 'Are you sure?',
    text: "You won't be able to revert this!",
    icon: 'warning',
    buttons: ["Cancel", true],
    closeOnClickOutside: false,
    dangerMode: true,
    }).then((willDelete) => {
    if (willDelete) {
    this.commonapi.delete_tags_api(tagvalue).subscribe(res=>{
      this.delete_tags_val = res;
      if(this.delete_tags_val.status === 'success'){
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
      },1500);}
      else{
        swal({
          icon: 'warning',
          title: this.delete_tags_val.status,
          text: this.delete_tags_val.message,

        })
      }
    })
  }
})
}
  closeModal(modalId){
    let modal = document.getElementById(modalId);
    modal.style.display = "none";
    $('.modal-backdrop').remove();
  }

public selectedtaglist:any;
BulkdeleteTag(){
  let taglist = "";
  taglist = this.getStringConcatinated(this.selectList);
  this.selectedtaglist = taglist;
  swal({
  title: 'Are you sure?',
  text: "You won't be able to revert this!",
  icon: 'warning',
  buttons: ["Cancel", true],
  closeOnClickOutside: false,
  dangerMode: true,
  }).then((willDelete) => {
  if (willDelete) {
  this.commonapi.delete_tags_api(this.selectedtaglist).subscribe(res=>{
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
selectList = [];
filterArr:any;
selectedCount:any=0;
selectTag(value) {
  this.filterArr = this.selectList.filter( h => h==value);
  if(this.filterArr.length == 0){
    this.selectList.push(value);
  }else{
    this.selectList = this.selectList.filter(item => item !== value);
  }
  this.selectedCount = this.selectList.length;
}
removeSelectedTag(){
  this.selectList = [];
  this.selectedCount = this.selectList.length;
  this.masterSelected = false;
  for (var i = 0; i < this.checklist.length; i++) {
    this.checklist[i].isSelected = false;
  }
}
checkUncheckAll() {
  for (var i = 0; i < this.checklist.length; i++) {
    this.checklist[i].isSelected = this.masterSelected;
    if(this.checklist[i].isSelected == true){
      this.filterArr = this.selectList.filter( h => h==this.checklist[i].value);
      if(this.filterArr.length == 0){
        this.selectList.push(this.checklist[i].value);
      }
    }
    else{
      this.selectList = this.selectList.filter(item => item !== this.checklist[i].value);
    }
  }
  this.selectedCount = this.selectList.length;
}
isAllSelected(id) {
  this.selectTag(id);
  this.masterSelected = this.checklist.every(function (item: any) {
    return item.isSelected == true;
  })
}

getStringConcatinated(array_object){
  //Join Array elements together to make a string of comma separated list
  let string_object = "";
  try{
    if (array_object.length>0){
      string_object = array_object[0];
      for (let index = 1; index < array_object.length; index++) {
        string_object = string_object+','+array_object[index];
      }
      return string_object
    }
  }
  catch(Error){
    return ""
  }
}
tableSearch(){
  this.searchTerm = (<HTMLInputElement>document.getElementById('customsearch')).value;
  this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
    dtInstance.destroy();
    this.dtTrigger.next();
  });
}
omitSpecialChar(event){
   return this.tagsValidation.omitSpecialChar(event)
}
validatePastedData(event){
  if(this.tagsValidation.validatePastedData(event)){
    this.errorMessageTag = ''
  }
  else{
    this.errorMessageTag = 'Accepts only alpha numeric characters with @._\-'
  }
}
}
