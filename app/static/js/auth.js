const authRoot=document.querySelector('#authApp');
if(authRoot){
  Vue.createApp({
    data:()=>({mode:authRoot.dataset.mode,loading:false,form:{username:'',email:'',password:'',role:'user'}}),
    methods:{async submit(){if(this.loading)return;this.loading=true;try{if(this.mode==='login'){const response=(await http.post('/auth/login',{username:this.form.username,password:this.form.password})).data.data;updateCsrfToken(response.csrf_token);window.location.assign(response.redirect);}else{const response=await http.post('/auth/register',this.form);await Swal.fire({icon:'success',title:'申請已送出',text:response.data.data.message});window.location.assign('/login');}}catch(e){await showFailure(e);}finally{this.loading=false;}}
    }
  }).mount(authRoot);
}
