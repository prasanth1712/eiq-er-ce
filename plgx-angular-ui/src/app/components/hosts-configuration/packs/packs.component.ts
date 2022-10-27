import { Component, OnInit } from '@angular/core';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { Router, ActivatedRoute, ActivatedRouteSnapshot } from '@angular/router';
import { FormControl, FormGroup, FormBuilder, Validators, FormArray } from '@angular/forms';
import swal from 'sweetalert';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import { Subject, Subscription } from 'rxjs';
import { Location } from '@angular/common';
import { DataTableDirective } from 'angular-datatables';
import { AuthorizationService } from '../../../dashboard/_services/Authorization.service';
import Swal from 'sweetalert2';
import { TagsValidationHandler } from '../../../dashboard/_helpers/tagsValidationHandler';
var packPaginationIndex;
var packPaginationLength;
class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}

@Component({
selector: 'app-packs',
templateUrl: './packs.component.html',
styleUrls: ['./packs.component.scss']
})
export class PacksComponent implements OnInit {
    packsfile: FormGroup;
    public pack_res_data: any;
    public pack: any;
    public pack_data: any;
    first_pack : any = [];
    packData: any = [];
    dataval:any;
    searchText:any;
    term:any;
    packs:File;
    submitted:any;
    category:any;
    selectedItem:any;
    result:any;
    error:any;
    Updated = false;
    packAddtagsVal:any;
    packRemovetagsVal:any;
    queriesAddtagVal:any;
    queriesRemovetagsVal:any;
    updatepackObj= {};
    packsCategoryDictionary = [];
    sortedPackDataName=[];
    PackName:string;
    dtElement: DataTableDirective;
    pack_details:any;
    pack_data_names = [];
    isDuplicateFile: boolean = true;
    maxFileSize: any;
    maxFileSizeMb: any;
    FileSizeError: boolean = false;
    isDtInitialized:boolean = false
    maxTagCharacters = (environment?.max_tag_size)? environment.max_tag_size : 64;
    role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess}
  errorMessageTag: string;
constructor(
private commonapi: CommonapiService,
private fb: FormBuilder,
private router: Router,
private http: HttpClient,
private _Activatedroute:ActivatedRoute,
private _location: Location,
private authorizationService: AuthorizationService,
private tagsValidation:TagsValidationHandler
) { }

clearValue:string = '';
clearInput() {
  this.clearValue = null;
}

getById(event, newValue,any){
    this.selectedItem = newValue;
    for(const i in this.pack_res_data?.data.results){
        if (this.pack_res_data?.data.results[i].name == any) {
            this.packData =this.pack_res_data?.data.results[i]
        }
    }
}

getfirstData(first_pack){
    this.packData = first_pack
    this.selectedItem = this.packData.name;
}

uploadFile(event){
    console.log(event);
    var file_name = event.target?.files[0]?.name;
    var file_name_without_extension = file_name.split('.').slice(0, -1).join('.');
    if(this.tagsValidation.isEmpty(file_name_without_extension)){
      swal({
        icon: 'warning',
        text: 'File name cannot be empty',
      }).then((willDelete) => {
        if (willDelete) {
          this.clearInput();
        }
      })
    }
    else{
      if (event.target.files.length > 0) {
        if(event.target.files[0].size > this.maxFileSize){
          this.close_add_pack_modal();
          Swal.fire({
            icon: 'warning',
            text: 'File size cannot be greater than ' + this.maxFileSizeMb  + 'MB'
            }).then((successOk) => {
              if(successOk){
                this.FileSizeError = true
                this.clearInput();
              }
            })
        }
        else{
          this.pack = event.target.files;
          this.FileSizeError = false
        }
      }
    }
}
openModal(){
  let modal = document.getElementById("add_pack");
  modal.style.display = "block";
}
deletePacks(pack_id, pack_name){
  swal({
    title: 'Are you sure?',
    text: "Want to delete the pack "+ pack_name+"?",
    icon: 'warning',
    buttons: ["Cancel", true],
    closeOnClickOutside: false,
    dangerMode: true,
    }).then((willDelete) => {
    if (willDelete) {
      this.commonapi.deleteApipacks(pack_id).subscribe(res =>{
        console.log(res);
        swal({
      icon: 'success',
      title: 'Deleted!',
      text: 'Pack has been deleted.',
      buttons: [false],
      timer: 2000
      })
      setTimeout(() => {
        this.rerender();
        this.router.navigateByUrl('/', {skipLocationChange: true}).then(()=>
        this.router.navigate(['/hostconfiguration/packs']));
      },300);
    })
  }
})
}


    packAddTag(test,id){
      this.commonapi.packs_addtag_api(id,test.toString()).subscribe(res => {
        this.packAddtagsVal = res ;
      });
    }
    packRemoveTag(event,pack_id) {
      this.commonapi.packs_removetags_api(pack_id,event).subscribe(res => {
        this.packRemovetagsVal = res ;
      });

    }
    queriesAddTag(tags,query_id){
      this.commonapi.queries_addtag_api(query_id,tags.toString()).subscribe(res => {
        this.queriesAddtagVal = res ;

      });
    }
    queriesRemoveTag(event,query_id) {
      this.commonapi.queries_removetags_api(query_id,event).subscribe(res => {
        this.queriesRemovetagsVal = res ;

      });

    }

runAdHoc(queryId){
    this.router.navigate(["/live-query/",queryId]);
}

ngOnInit() {
  this.getAllPacks();
 this.maxFileSize = 2000000;
 this.maxFileSizeMb = 2;
 this._Activatedroute.queryParams.subscribe(params => {
   this.PackName = this._Activatedroute.snapshot.queryParams["packname"];
   this.packsfile = this.fb.group({
    pack: '',
    category:'General'
  });
  this.pack=this.packsfile.value.pack;
  if(this.PackName){
    this.getPack({searching:false,paging:false});
  }else{
    this.rerenderPacks();
    this.getPack({searching:true,paging:true});
}
 })
   
}
rerenderPacks(){
  if (this.isDtInitialized) {
    this.dtElement?.dtInstance?.then((dtInstance: DataTables.Api) => {
      dtInstance.destroy();
      this.dtTrigger.next();
    });
  } else {
    this.isDtInitialized = true
    this.dtTrigger.next();
  }
}
packList:any;
dtOptions: DataTables.Settings = {};
errorMessage:any;
dtTrigger: Subject<any> = new Subject();
getPack({searching,paging}){
  this.dtOptions = {
    pagingType: 'full_numbers',
    pageLength: 10,
    serverSide: true,
    processing: true,
    searching: true,
    lengthChange: false,
    paging:true,
    info:false,
    scrollCollapse: true,
    "language": {
      "search": "Search: "
    },
    ajax: (dataTablesParameters: any,callback) => {
      var body = dataTablesParameters;
      packPaginationIndex=body['start']
        packPaginationLength = body['length']
      if(packPaginationLength != 10){
        dataTablesParameters.start = 0
        body['length'] = 10
        body['start'] = 0
      }
      if(body.search.value!= ""  &&  body.search.value.length>=1){
         body['searchterm']=body.search.value;
         body['limit']=body['length'];
      }
      if(this.PackName){
        $('#packstable_filter').hide();
        body['searchterm']=this.PackName
      }
      else if(body['searchterm']==undefined){
          body['searchterm']="";
          body['limit']=body['length'];
      }
      this.sortedPackDataName=[];
      $('.placeholder_event').hide();
      $('.show_packs_data').show();
      this.http.post<DataTablesResponse>(environment.api_url+"/packs", body,{ headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res =>{
        this.packList = res.data['results'];
        this.packsCategoryDictionary = [];
      if(this.packList.length >0 &&  this.packList!=undefined){
        this.packList = res.data['results'];
        this.packList.sort((x,y) => y.name - x.name)
        $('.dataTables_paginate').show();
        var tblpagination = document.getElementById("packstable_paginate");
          tblpagination?.parentElement?.classList?.remove("col-md-7");
          tblpagination?.parentElement?.classList?.add("col-md-12");
          this.pack_res_data = res;
        for(const i in this.pack_res_data?.data.results){
          let is_present = false;
          for(const j in this.packsCategoryDictionary){
            if(this.pack_res_data?.data.results[i].category == this.packsCategoryDictionary[j]['category']){
              is_present = true;
              if(this.pack_res_data?.data.results[i].name in this.packsCategoryDictionary[j]['packs']){
                break;
              }else{
                this.packsCategoryDictionary[j]['packs'].push(this.pack_res_data?.data.results[i].name);
              }
            }
          }
          if(is_present == false){
            this.packsCategoryDictionary.push({'category':this.pack_res_data?.data.results[i].category, 'packs': [this.pack_res_data?.data.results[i].name]});
          }
        }
        for(const item_index in this.packsCategoryDictionary){
          this.packsCategoryDictionary[item_index]['packs'] = this.getSortedPackArray(this.packsCategoryDictionary[item_index]['packs']);
        }
        this.sortedPackDataName = this.packsCategoryDictionary[0]['packs'];
        for(const i in this.pack_res_data?.data.results){
            if (this.pack_res_data?.data.results[i].name == this.packsCategoryDictionary[0]['packs'][0]){
                this.getfirstData(this.pack_res_data?.data.results[i]);
            }
        }
      }else{
        if(body.search.value=="" || body.search.value == undefined){
          this.errorMessage = "No results found";
          $('.dataTables_paginate').hide();
        }
        else{
          this.errorMessage = "No search results found";
          $('#packstable_wrapper')?.hide();
          $('.dataTables_paginate').hide();
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
    columns: [{data: 'Packs' }]
  }
}

ngAfterViewInit(): void {
  this.dtTrigger.next();
}

ngOnDestroy(): void {
  this.dtTrigger.unsubscribe();
}

get f() { return this.packsfile.controls; }


onSubmit() {
  if (this.pack[0]==null){
    this.close_add_pack_modal();
    swal(
      "Please select a file for upload"
    )
  }
    this.category = this.packsfile.value.category;
    this.pack_data = this.pack;
    this.submitted = true;
    if (this.packsfile.invalid) {
        return;
    }
    var file_name_without_extension = this.pack[0].name.split('.').slice(0, -1).join('.');
    if (this.pack_data_names.includes(file_name_without_extension.toLowerCase())){
      this.isDuplicateFile = false;
      swal({
        icon: 'warning',
        title: "Name already exist",
        text: "Name already exist , are you sure you want to continue ?",
        buttons: ["Cancel", true],
        closeOnClickOutside: false,
        dangerMode: true,
        }).then((confirm) => {
          if(confirm){
            this.isDuplicateFile = true;
            this.upload_pack();
            this.clearInput();
            this.close_add_pack_modal();
          }
          else {
            this.isDuplicateFile = false;
            this.clearInput();
          }
        })
    }
    else {
      this.isDuplicateFile = true;
      this.upload_pack();
      this.close_add_pack_modal();
      this.clearInput();
    }
}
upload_pack(){
  this.commonapi.pack_upload_api(this.pack, this.category).subscribe(res =>{
    this.result=res;
    if(this.result && this.result.status === 'failure'){
        swal({
        icon: 'warning',
        title: this.result.status,
        text: this.result.message,

        })
        this.clearInput()
        this.close_add_pack_modal();
    }else{
        swal({
        icon: 'success',
        title: this.result.status,
        text: this.result.message,
        buttons: [false],
        timer: 2000
        })
    this.error = null;
    this.Updated = true;
    this.rerender();
    }
    },
    error => {
      if(error.status == 413){
        Swal.fire({
          icon: 'error',
          text: 'Request entity is too large, please upload file less than ' + (this.maxFileSize / 1048576).toFixed(2) + 'MB'
        })
        this.close_add_pack_modal();
      }
      else{
        Swal.fire({
          icon: 'error',
          text: error.statusText
        })
        this.close_add_pack_modal();
      }
    })
}

redirect(pack) {
    console.log(pack);
    this.router.navigate(['/tag']);
}
getAllPacks(){
  this.commonapi.packs_api().subscribe((res: any) => {
    this.pack_details = res.data.results;
    for(const i in this.pack_details){
      this.pack_data_names.push(this.pack_details[i].name)
    }

  });
}

getSortedPackArray(list){
  let  pack_names = [];
  let  pack_names_lowercase = [];
  let pack_name_sorted_list = [];
  let list_to_return = [];
  for(const pack_name_index in list){
    pack_names_lowercase.push(list[pack_name_index].toLowerCase());
  }
  pack_name_sorted_list  = pack_names_lowercase.sort();
  pack_name_sorted_list = pack_name_sorted_list.filter((el, i, a) => i === a.indexOf(el))

  for(const index in pack_name_sorted_list){
    for(const index2 in list){
      if(pack_name_sorted_list[index]==list[index2].toLowerCase()){
        list_to_return.push(list[index2]);
      }
    }
  }
  list_to_return = list_to_return.filter((el, i, a) => i === a.indexOf(el))

  return list_to_return
}

goBack(){
  this._location.back();
}
rerender(): void {
  var table = $("#packstable").DataTable();
  table.destroy();
  this.dtTrigger.next();
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
   'errorMsg': 'Tag should not be more then ' + this.maxTagCharacters + ' characters'
 };
 omitSpecialChar(event){
  this.errorMessageTag = '';
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
 close_add_pack_modal() {
  this.submitted = false;
  this.packsfile.setValue({
    pack: '',
    category:'General'
  });
  const body = document.querySelector("body");
  body.style.overflow = "auto";
  let modal = document.getElementById("add_pack");
  modal.style.display = "none";
  }
}
