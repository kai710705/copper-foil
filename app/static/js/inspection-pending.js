Vue.createApp({
  data:()=>({items:[],loading:false,error:'',busyId:null}),
  methods:{
    async load(){this.loading=true;this.error='';try{this.items=(await window.http.get('/inspections?pending=1')).data.data;}catch(e){this.error=window.apiErrorMessage(e);}finally{this.loading=false;}},
    async review(id,status){this.busyId=id;try{await window.http.patch(`/inspections/${id}/review`,{status});this.items=this.items.filter(item=>item.id!==id);await Swal.fire({icon:'success',title:'已更新處理狀態',timer:1200,showConfirmButton:false});}catch(e){window.showFailure(e);}finally{this.busyId=null;}}
  },mounted(){this.load()}
}).mount('#pendingApp');
