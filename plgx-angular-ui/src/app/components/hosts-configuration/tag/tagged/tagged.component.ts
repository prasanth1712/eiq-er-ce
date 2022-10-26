import { Component, OnInit } from '@angular/core';
import { CommonapiService } from '../../../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../../../dashboard/_services/commonvariable.service';
import { Router, ActivatedRoute } from '@angular/router';
import swal from 'sweetalert';
import { Location } from '@angular/common';
import { Title } from '@angular/platform-browser';
import { AngularMultiSelect } from 'angular2-multiselect-dropdown';
import { FormControl,FormGroup, FormBuilder, Validators } from '@angular/forms';
import { AuthorizationService } from '../../../../dashboard/_services/Authorization.service';
import { environment } from '../../../../../environments/environment';
export interface CustomResponse {
  data: any;
  message: any;
  status: any;
}

@Component({
  selector: 'app-tagged',
  templateUrl: './tagged.component.html',
  styleUrls: ['./tagged.component.scss']
})

export class TaggedComponent implements OnInit {
  id: any;
  sub: any;
  query_data: any;
  first_query: any = [];
  first_pack: any = [];
  host_data_val: any;
  pack_data_val: any;
  query_data_val: any;
  public tags_val: any;
  tags_data: any;
  tagged: any;
  urlString = "";
  pack_data: any;
  packdata_tags: any;
  packdata_id: any;
  packdata_name: any;
  term_query: any;
  term_pack: any;
  pack_tags_val: any;
  hosts_addtags_val: any;
  hosts_removetags_val: any;
  pack_addtags_val: any;
  pack_removetags_val: any;
  queries_addtags_val: any;
  queries_removetags_val: any;
  selectedItem_query:number;
  SelectorForm: FormGroup;
  hostDropdownList = new Array();
  hostData: any = new Array();
  hostDropdownSettings = {};
  responseData: any;
  resResults: any;
  osNameList = [];
  osNameListSettings = {};
  selectedHosts:any;
  selectedosName:any;
  tagAssignUpdateRes:any;
  maxTagCharacters = (environment?.max_tag_size)? environment.max_tag_size : 64;
  role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess}
  constructor(
    private commonapi: CommonapiService,
    private commonvariable: CommonVariableService,
    private _Activatedroute: ActivatedRoute,
    private router: Router,
    private _location: Location,
    private titleService: Title,
    private fb: FormBuilder,
    private authorizationService: AuthorizationService,
  ) { }

  getById(query_id) {
    this.selectedItem_query=query_id
    for (const i in this.query_data_val) {
      if (this.query_data_val[i].id == query_id) {
        this.query_data = this.query_data_val[i]
      }
    }
  }

  getfirst_data() {
    if (this.tagged.data.queries.length > 0) {
      this.query_data = this.tagged.data.queries[0];
      this.selectedItem_query=this.query_data.id
    }
  }

  getById_pack(pack_name) {
    for (const i in this.pack_data_val) {
      if (this.pack_data_val[i].name == pack_name) {
        this.pack_data = this.pack_data_val[i];
        this.packdata_tags = this.pack_data.tags;
        this.packdata_id = this.pack_data.id;
        this.packdata_name = this.pack_data.name;
      }
    }
  }

  getfirstpack_data() {
    this.pack_data = this.tagged.data.packs[0];
    this.packdata_tags = this.pack_data.tags;
    this.packdata_id = this.pack_data.id;
    this.packdata_name = this.pack_data.name;
  }
  ngOnInit() {
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Tags");

    this.sub = this._Activatedroute.paramMap.subscribe(params => {
      this.id = params.get('id');
    });

    this.urlString =decodeURIComponent(this.router.url);
    let toArray = this.urlString.split('/');
    this.tags_val = toArray[4];
    this.getTagData();
    this.SelectorForm = this.fb.group({
     hostName: [''],
     osName:['']
    });
   this.hostList();
   this.osNameSelect();
  }

  packsCategoryDictionary = [];
  tempPacksCategoryDictionary = [];
   getTagData(){
     var qrytags_val = this.tags_val;
     this.commonapi.tagged_api(qrytags_val).subscribe((res: any) => {
       this.packsCategoryDictionary = [];
       this.tagged = res;
       this.first_pack = res;
       if(this.tagged.status == "failure"){
         this.pagenotfound();
       }
       else{
       this.host_data_val = this.tagged.data.hosts;
       this.pack_data_val = this.tagged.data.packs;
       this.query_data_val = this.tagged.data.queries;
       for(const i in this.pack_data_val){
         let ispresent = false;
         for(const j in this.packsCategoryDictionary){
           if(this.pack_data_val[i].category == this.packsCategoryDictionary[j]['category']){
             ispresent = true;
             if(this.pack_data_val[i].name in this.packsCategoryDictionary[j]['packs']){
               break;
             }else{
               this.packsCategoryDictionary[j]['packs'].push(this.pack_data_val[i].name);
             }
           }
         }
         if(ispresent == false){
           this.packsCategoryDictionary.push({'category':this.pack_data_val[i].category, 'packs': [this.pack_data_val[i].name]});
         }
       }
       this.tempPacksCategoryDictionary = this.packsCategoryDictionary;
         if (this.tagged.data.queries.length > 0) {
           this.getfirst_data()
         }

       if (this.tagged.data.packs.length > 0) {
         this.getfirstpack_data()
       }
      }
     });
   }

  get v() { return this.SelectorForm.controls; }
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
  pack_removeTag(event, pack_id) {
    this.commonapi.packs_removetags_api(pack_id, event).subscribe(res => {
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

  runAdHoc(queryId) {
    this.router.navigate(["/live-query/", queryId]);
  }
  pagenotfound() {
      this.router.navigate(['/pagenotfound']);
  }

  hostList(){
      this.commonapi.Hosts_main().subscribe((res: CustomResponse) => {
        this.responseData = res;
        this.resResults = this.responseData.data.results
        for (const i in this.resResults) {
          if(this.resResults[i].os_info.platform!="darwin" &&  this.resResults[i].is_active){
           this.hostData.push({id: this.resResults[i].host_identifier, itemName :this.resResults[i].display_name}) ;
          }
        }
        this.hostDropdownList = this.hostData;
        this.hostDropdownSettings = {
          singleSelection: false,
          text:"Select Host(s)",
          selectAllText:'Select All',
          unSelectAllText:'UnSelect All',
          enableSearchFilter:true,
          lazyLoading: false,
          classes: "angular-multiselect-class",
          searchPlaceholderText: "Search Hosts here..",
          badgeShowLimit:1
        };

      });
  }

  osNameSelect(){
    this.commonapi.Hosts_data().subscribe((res: CustomResponse) => {
      var listOfOs=[]
      for (const i in res.data.results) {
        listOfOs.push(res.data.results[i]['os_info'].name)
      }
      listOfOs =listOfOs.filter((value,index)=>listOfOs.indexOf(value)===index)
      for(const i in listOfOs){
        this.osNameList.push({id:i, itemName:listOfOs[i]});
      }
      this.osNameListSettings = {
         singleSelection: false,
         text: "Select by Operating System(s)",
         selectAllText: 'Select All OS Names',
         unSelectAllText: 'Unselect All',
         badgeShowLimit: 1,
         enableSearchFilter: true,
         classes: "os-class",
         searchPlaceholderText: "Search OS Name here.."
       };
   });
  }

  OpenAssignModal(){
    const body = document.querySelector("body");
    body.style.overflow = "hidden";
    let modal = document.getElementById("tagsBulkAssignModal");
    modal.style.display = "block";
  }

  closeAssignModal() {
    const body = document.querySelector("body");
    body.style.overflow = "auto";
    let modal = document.getElementById("tagsBulkAssignModal");
    modal.style.display = "none";
    this.onDeSelectAllHostName();
    this.onDeSelectAllOsName();
  }
  closeModal(modalId){
    let modal = document.getElementById(modalId);
    modal.style.display = "none";
    $('.modal-backdrop').remove();
  }

  onSubmit(){
      let hostName = this.v.hostName.value;
      let osName = this.v.osName.value;
      this.selectedHosts = this.hostIdentifierFilter(hostName);
      this.selectedosName = this.addSelectedFilter(osName);
      var tagName = this.tags_val;
      var body = {"hosts":this.selectedHosts,"os_names":this.selectedosName};
      if( hostName.length !== 0 || osName.length !== 0){
        this.commonapi.tagsBulkAssignApi(body,tagName).subscribe(res => {
           this.tagAssignUpdateRes = res;
           if(this.tagAssignUpdateRes.status === 'success'){
             swal({
               icon: 'success',
               title: this.tagAssignUpdateRes.status,
               text: this.tagAssignUpdateRes.message,
               buttons: [false],
               timer: 2000
             })
             this.getTagData();
             this.closeAssignModal();
           }
           else{
             swal({
               icon: 'warning',
               title: this.tagAssignUpdateRes.status,
               text: this.tagAssignUpdateRes.message,
             })
             this.closeAssignModal();
           }
        });
      }
      else{
        swal({
           icon: 'warning',
           text:  "Please Select Host/Operating System" ,
         })
      }

  }

  addSelectedFilter(selectedFilter){
    var arrayList = [];
    for (const i in selectedFilter) {
      arrayList.push(selectedFilter[i].itemName);
    }
    return arrayList;
  }

  hostIdentifierFilter(selectedFilter){
    var arrayList = [];
    for (const i in selectedFilter) {
      arrayList.push(selectedFilter[i].id);
    }
    return arrayList;
  }

  onDeSelectAllHostName(items?: any){
    this.SelectorForm.controls['hostName'].reset()
    this.SelectorForm.get('hostName').setValue([]);
  }

  onDeSelectAllOsName(items?: any){
    this.SelectorForm.controls['osName'].reset()
    this.SelectorForm.get('osName').setValue([]);
  }
  private tagValidation(control: FormControl) {
    var maxTagInput = (environment?.max_tag_size)? environment.max_tag_size : 64;
    if (control.value.length > maxTagInput ) {
        return { 'errorMsg': true };
    }
    return null;
  }
  public validators = [this.tagValidation];
  public errorMessages = {
    'errorMsg': 'Tag should not be more than ' + this.maxTagCharacters + ' characters'
  };
  navigatePacks(pack_name){
    this.router.navigate(['/hostconfiguration/packs'],{queryParams:{packname: pack_name}});
}
 searchPack(searchTerm){
    var arrayPackDictionary = [];
    this.packsCategoryDictionary = this.tempPacksCategoryDictionary;
    this.packsCategoryDictionary.forEach(function (packitem) {
      var filterpackDictionary = packitem.packs.filter(n => n.includes(searchTerm));
      var filterCategoryDictionary = packitem.category.includes(searchTerm);
      if(filterpackDictionary.length > 0 || filterCategoryDictionary == true){
        arrayPackDictionary.push({'category':packitem.category,'packs':packitem.packs})
       }
     });
     this.packsCategoryDictionary = arrayPackDictionary;
  }
}
