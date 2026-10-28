window.http=axios.create({baseURL:'/api/v1',timeout:120000,headers:{Accept:'application/json'}});
http.interceptors.request.use(config=>{const method=(config.method||'get').toUpperCase();if(['POST','PATCH','PUT','DELETE'].includes(method)){const token=document.querySelector('meta[name="csrf-token"]')?.content;if(token)config.headers['X-CSRF-Token']=token;}return config;});
window.updateCsrfToken=token=>{if(token)document.querySelector('meta[name="csrf-token"]').content=token;};
window.apiErrorMessage=e=>e.response?.data?.error?.message||e.response?.data?.message||(e.code==='ECONNABORTED'?'伺服器回應逾時，請重試。':'連線失敗，請檢查服務後重試。');
window.showFailure=e=>Swal.fire({icon:'error',title:'操作未完成',text:apiErrorMessage(e)});
window.stateLabel=value=>({pending:'待審核',approved:'已核准',rejected:'已拒絕',disabled:'已停用',open:'待處理',resolved:'已處理',completed:'已完成'}[value]||value);
