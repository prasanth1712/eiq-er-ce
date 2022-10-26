
import { AfterViewInit,Component, OnInit ,ViewChild} from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import {CommonapiService} from '../../../dashboard/_services/commonapi.service';
import swal from 'sweetalert';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import { DataTableDirective } from 'angular-datatables';
import { Subject } from 'rxjs';
import { AuthorizationService } from '../../../dashboard/_services/Authorization.service';
import { FormControl, FormGroup, FormBuilder, Validators, FormArray } from '@angular/forms';
import { TagsValidationHandler } from '../../../dashboard/_helpers/tagsValidationHandler';

class DataTablesResponses {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}


@Component({
  selector: 'app-queries',
  templateUrl: './queries.component.html',
  styleUrls: ['./queries.component.scss']
})
export class QueriesComponent implements AfterViewInit,OnInit {
  @ViewChild(DataTableDirective)
  dtElement: DataTableDirective;
  dtInstance: DataTables.Api;
  dtOptions: DataTables.Settings = {};
  dtTrigger: Subject<any> = new Subject();
  id:any;
  sub:any;
  public queries: any;
  queryData: any;
  queryId:any;
  queriesData:any;
  queriesDataList:any;
  selectedItem:any;
  queriesAddTagsval:any;
  queriesRemoveTagsval:any;
  sortedPackDataNameId=[];
  AsssortedPackDataNameId=[];
  firstData:any;
  queryAllErrorMessage:any;
  errorMessage:any;
  queriesTypeId = "associatedPacksId";
  emptyMsg:string;
  maxTagCharacters = (environment?.max_tag_size)? environment.max_tag_size : 64;
  role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess}
  errorMessageTag: string;

  constructor(
    private _Activatedroute:ActivatedRoute,
    private commonapi: CommonapiService,
    private router: Router,
    private http: HttpClient,
    private authorizationService: AuthorizationService,
    private tagsValidation:TagsValidationHandler
  ) { }

   getByIdQueries(event, newValue,query_id){
    this.selectedItem = newValue;
     for(const i in this.queriesData.data.results){
       this.queryId = query_id;
          if (this.queriesData.data.results[i].id == query_id){
            this.queryData =this.queriesData.data.results[i]
            if (this.queryData.platform==null){
              this.queryData.platform="all"
            }

          }
      }
   }
   getFirstData(any){
           this.queryData = any;
           this.selectedItem = this.queryData.id;
           this.queryId=this.queryData.id
           if (this.queryData.platform==null){
            this.queryData.platform="all"
          }
    }

  queriesAddTag(tags,query_id){
    this.commonapi.queries_addtag_api(query_id,tags.toString()).subscribe(res => {
      this.queriesAddTagsval = res ;
    });
  }
  queriesRemoveTag(event,query_id) {
    this.commonapi.queries_removetags_api(query_id,event).subscribe(res => {
      this.queriesRemoveTagsval = res ;
    });
  }

  runAdHoc(queryId){
     this.router.navigate(["/live-query/",queryId]);
   }

  rerender(): void {
        this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
        dtInstance.destroy();
        this.dtTrigger.next();
      });
   }

  typeQuery(id_of_packs){
     this.queriesTypeId = id_of_packs
     this.rerender()
  }

  ngOnInit() {
    this.sub = this._Activatedroute.paramMap.subscribe(params => {
      this.id = params.get('id');
    });
    $('.queriesDataListDiv').show();
    $('.queries_body').hide();
    this.GetQueriesData();
  }

  GetQueriesData(){
    this.dtOptions = {
      pagingType: 'full_numbers',
      pageLength: 10,
      serverSide: true,
      processing: true,
      destroy: true,
      searching: true,
      lengthChange: false,
      info:false,
      scrollCollapse: true,
      "language": {
        "search": "Search: "
      },
      dom: "<'row'<'col-sm-12'f>>" +
      "<'row'<'col-sm-12'tr>>" +
      "<'row table-controls'<'col-sm-12 queries-pagination-controls'p>>",
      ajax: (dataTablesParameters: any,callback) => {
        var body = dataTablesParameters;
        body['limit']=body['length'];
        if(body.search.value!= ""  &&  body.search.value.length>=1){
           body['searchterm']=body.search.value;
        }
        if(body['searchterm']==undefined){
            body['searchterm']="";
        }

        var apiName
        if(this.queriesTypeId == 'allQueriesId'){ apiName="/queries" }
        else{ apiName="/queries/packed" }

        this.http.post<DataTablesResponses>(environment.api_url+apiName, body,{ headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res =>{
          this.queriesData = res;
          this.queriesDataList = this.queriesData.data.results;
          if(this.queriesDataList.length >0 &&  this.queriesDataList!=undefined){
             $('.dataTables_paginate').show();
             $('.queriesDataListDiv').show();
             $('.queries_body2').hide();
             if(this.queriesData.data.count == 0 && this.queriesTypeId == 'associatedPacksId'){
               this.showEmptyMsg('No Queries Associated with Packs');
             }
             else if(this.queriesData.data.count == 0 && this.queriesTypeId == 'allQueriesId'){
               this.showEmptyMsg('No Queries Present');
             }
             else{
               $('.emptyMsgDiv').hide();
               $('.queries_body').show();
              }
              this.sortedPackDataNameId=[];
              let dataval_sort=[]
              for (const i in this.queriesData.data.results){
                var name = this.queriesData.data.results[i].name
                dataval_sort.push(name.toLowerCase())
              }
              let  dataval_sorted=[];
              dataval_sorted=dataval_sort.sort()
              dataval_sorted = dataval_sorted.filter((el, i, a) => i === a.indexOf(el))
              for(const j in dataval_sorted){
               for(const i in this.queriesData.data.results){
                var name = this.queriesData.data.results[i].name
                  if(name.toLowerCase() == dataval_sorted[j]){
                    let sorted_name_id=[]
                    sorted_name_id.push(this.queriesData.data.results[i].name)
                    sorted_name_id.push(this.queriesData.data.results[i].id)
                    this.sortedPackDataNameId.push(sorted_name_id)
                    }
                }
              }
              for(const i in this.queriesData.data.results){
                let name = this.queriesData.data.results[i].name
               if(name.toLowerCase() == dataval_sorted[0]){
                this.firstData=this.queriesData.data.results[i]
              }
             }
             this.getFirstData(this.firstData);
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
      columns: [{data: 'queriesdata' }]
    }
  }

  deleteQueries(query_id, query_name){
    swal({
      title: 'Are you sure?',
      text: "Want to delete the Query "+ query_name,
      icon: 'warning',
      buttons: ["Cancel", true],
      closeOnClickOutside: false,
      dangerMode: true,
      }).then((willDelete) => {
      if (willDelete) {
        this.commonapi.deleteApiQueries(query_id).subscribe(res =>{
          if(res['status']=="Success"){
            swal({
              icon: 'success',
              title: 'Deleted!',
              text: 'Query has been deleted.',
              buttons: [false],
              timer: 2000
            })
            this.rerender();
          }else{
            swal({
              icon: 'warning',
              title: res['status'],
              text: res['message'],
              buttons: [false],
              timer: 2000
            })
          }
      })
    }
  })
  }

  showEmptyMsg(msg){
    this.emptyMsg = msg;
    $('.emptyMsgDiv').show();
    $('.queriesDataListDiv').hide();
  }

  ngAfterViewInit(): void {
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
  navigatePacks(pack_name){
      this.router.navigate(['/hostconfiguration/packs'],{queryParams:{packname: pack_name}});
  }
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
}
