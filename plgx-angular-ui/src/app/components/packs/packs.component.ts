import { Component, OnInit } from '@angular/core';
import { CommonapiService } from '../../dashboard/_services/commonapi.service';
import { Router, ActivatedRoute } from '@angular/router';
import { FormControl, FormGroup, FormBuilder, Validators, FormArray } from '@angular/forms';
import swal from 'sweetalert';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Subject, Subscription } from 'rxjs';
import { Location } from '@angular/common';
import { DataTableDirective } from 'angular-datatables';
import { AuthorizationService } from '../../dashboard/_services/Authorization.service';
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
    public pack: any;
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
    role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess}
constructor(
private commonapi: CommonapiService,
private fb: FormBuilder,
private router: Router,
private http: HttpClient,
private _Activatedroute:ActivatedRoute,
private _location: Location,
private authorizationService: AuthorizationService,
) { }

clearValue:string = '';
clearInput() {
  this.clearValue = null;
}

getById(event, newValue,any){
    this.selectedItem = newValue;
    for(const i in this.pack.data.results){
        if (this.pack.data.results[i].name == any) {
            this.packData =this.pack.data.results[i]
        }
    }
}

getfirstData(first_pack){
    this.packData = first_pack
    this.selectedItem = this.packData.name;
}

uploadFile(event){
    console.log(event);
    if (event.target.files.length > 0) {
        this.pack = event.target.files;
    }
}
deletePacks(pack_id, pack_name){
  swal({
    title: 'Are you sure?',
    text: "Want to delete the pack "+ pack_name+"!",
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
    this.router.navigate(["/live-queries/",queryId]);
}

ngOnInit() {
  this._Activatedroute.paramMap.subscribe(params => {  
    this.PackName=params.get('packname')
    console.log(this.PackName," this.PackName")
  })
    this.packsfile = this.fb.group({
        pack: '',
        category:'General'
      });
    this.pack=this.packsfile.value.pack;
    if(this.PackName){
      this.getPack({searching:false,paging:false});
    }else{
      this.getPack({searching:true,paging:true});
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
    searching: searching,
    lengthChange: false,
    paging:paging,
    info:false,
    scrollCollapse: true,
    "language": {
      "search": "Search: "
    },
    ajax: (dataTablesParameters: any,callback) => {
      var body = dataTablesParameters;
      if(body.search.value!= ""  &&  body.search.value.length>=1){
         body['searchterm']=body.search.value;
         body['limit']=body['length'];
      }
      if(this.PackName){
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
        this.pack = res;
        for(const i in this.pack.data.results){
          let is_present = false;
          for(const j in this.packsCategoryDictionary){
            if(this.pack.data.results[i].category == this.packsCategoryDictionary[j]['category']){
              is_present = true;
              if(this.pack.data.results[i].name in this.packsCategoryDictionary[j]['packs']){
                break;
              }else{
                this.packsCategoryDictionary[j]['packs'].push(this.pack.data.results[i].name);
              }
            }
          }
          if(is_present == false){
            this.packsCategoryDictionary.push({'category':this.pack.data.results[i].category, 'packs': [this.pack.data.results[i].name]});
          }
        }
        for(const item_index in this.packsCategoryDictionary){
          this.packsCategoryDictionary[item_index]['packs'] = this.getSortedPackArray(this.packsCategoryDictionary[item_index]['packs']);
        }
        this.sortedPackDataName = this.packsCategoryDictionary[0]['packs'];
        for(const i in this.pack.data.results){
            if (this.pack.data.results[i].name == this.packsCategoryDictionary[0]['packs'][0]){
                this.getfirstData(this.pack.data.results[i]);
            }
        }
      }else{
        if(body.search.value=="" || body.search.value == undefined){
          this.errorMessage = "No results found";
          $('.dataTables_paginate').hide();
        }
        else{
          this.errorMessage = "No search results found";
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

get f() { return this.packsfile.controls; }



onSubmit() {
  if (this.pack[0]==null){
    swal(
      "Please select a file for upload"
    )
  }
    this.category = this.packsfile.value.category;
    this.submitted = true;
    if (this.packsfile.invalid) {
        return;
    }

  this.commonapi.pack_upload_api(this.pack, this.category).subscribe(res =>{
    this.result=res;
    if(this.result && this.result.status === 'failure'){
        swal({
        icon: 'warning',
        title: this.result.status,
        text: this.result.message,

        })
        this.clearInput()

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
    setTimeout(() => {
      this.ngOnInit()
    },1000)
    },
    error => {
    console.log(error);
    })
}

redirect(pack) {
    console.log(pack);
    this.router.navigate(['/tag']);
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

}
