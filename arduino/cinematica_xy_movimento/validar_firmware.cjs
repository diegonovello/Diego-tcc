// Teste do HEX AVR em avr8js 0.21.1. Nao conecta hardware e nao comprova fisica.
// Uso: NODE_PATH=<node_modules> node validar_firmware.cjs bloqueado.hex liberado.hex
// O segundo HEX deve ser compilado em COPIA TEMPORARIA com os quatro flags true.
// Nunca gravar essa copia de teste no Arduino sem calibrar a montagem.
const fs = require('node:fs');
const assert = require('node:assert/strict');
const {CPU, avrInstruction, AVRTimer, timer0Config, AVRUSART, usart0Config,
       AVRIOPort, portBConfig, portDConfig} = require('avr8js');

function hexWords(file) {
  const bytes = new Uint8Array(32768);
  let base = 0;
  for (const line of fs.readFileSync(file,'utf8').trim().split(/\r?\n/)) {
    const b = Buffer.from(line.slice(1),'hex');
    assert.equal([...b].reduce((s,v)=>(s+v)&255,0),0,'checksum HEX');
    const n=b[0], addr=(b[1]<<8)|b[2], type=b[3];
    if(type===0) bytes.set(b.subarray(4,4+n),base+addr);
    else if(type===4) base=((b[4]<<8)|b[5])*65536;
  }
  return new Uint16Array(bytes.buffer);
}

function machine(file) {
  const cpu = new CPU(hexWords(file),2048);
  new AVRTimer(cpu,timer0Config);
  const b = new AVRIOPort(cpu,portBConfig), d = new AVRIOPort(cpu,portDConfig);
  const uart = new AVRUSART(cpu,usart0Config,16000000);
  b.setPin(0,false); // D8: contato NC fechado
  let output='', capture=false;
  const counts=[0,0,0], starts=[null,null,null], last=[null,null,null];
  const order=[];
  let minWidth=Infinity, minPeriod=Infinity;
  uart.onByteTransmit = v => { output += String.fromCharCode(v); };
  d.addListener((value,old)=>{
    if(!capture) return;
    const active=(~value)&0x1c;
    assert.equal(active&(active-1),0,'dois STEP ativos ao mesmo tempo');
    for(let i=0;i<3;i++) {
      const bit=1<<(i+2);
      if((old&bit) && !(value&bit)) {
        assert(starts.every((s,j)=>j===i||s===null),'sobreposicao de pulsos');
        if(order.at(-1)!==i) order.push(i);
        const positive=!(value&(1<<(i+5))); // DIR_RECOLHER_LOW=true nesta configuracao
        counts[i]+=positive?1:-1;
        starts[i]=cpu.cycles;
        if(last[i]!==null) minPeriod=Math.min(minPeriod,cpu.cycles-last[i]);
        last[i]=cpu.cycles;
      }
      if(!(old&bit) && (value&bit) && starts[i]!==null) {
        minWidth=Math.min(minWidth,cpu.cycles-starts[i]); starts[i]=null;
      }
    }
  });
  function until(condition,seconds=3) {
    const end=cpu.cycles+seconds*16000000;
    while(!condition()) {
      if(cpu.cycles>=end) throw Error('Timeout AVR: '+output.slice(-600));
      avrInstruction(cpu); cpu.tick();
    }
  }
  function run(seconds) {
    const end=cpu.cycles+seconds*16000000;
    until(()=>cpu.cycles>=end,seconds+.1);
  }
  function send(s) {
    for(const c of Buffer.from(s)) {
      until(()=>!uart.rxBusy);
      assert(uart.writeByte(c));
      run(.00025); // deixa o byte chegar ao ISR e ao parser
    }
  }
  function expectCommand(command,needle,seconds=3) {
    output=''; send(command+'\n'); until(()=>output.includes(needle),seconds); run(.03);
  }
  until(()=>output.includes('Verificar confirmacoes em config.')); run(.05);
  capture=true;
  return {cpu,b,d,uart,counts,starts,order,until,run,send,expectCommand,
          get output(){return output;}, clear(){output='';},
          get minWidth(){return minWidth/16;},get minPeriod(){return minPeriod/16;}};
}

const [lockedFile,unlockedFile]=process.argv.slice(2);
assert(lockedFile&&unlockedFile,'Informar HEX bloqueado e HEX liberado apenas para emulacao.');
let m=machine(lockedFile);
m.expectCommand('referenciar RETO','Referencia MANUAL aceita.');
m.expectCommand('armar','BLOQUEADO');
m.expectCommand('caso 3','0;0;84');
m.expectCommand('mover','BLOQUEADO');
assert.deepEqual(m.counts,[0,0,0]);
console.log('PASS: configuracao distribuida bloqueia pulsos mesmo apos referencia e armar.');

m=machine(unlockedFile);
m.expectCommand('caso 3','0;0;84');
m.expectCommand('mover','BLOQUEADO');
m.b.setPin(0,true);
m.expectCommand('referenciar RETO','BLOQUEADO');
m.b.setPin(0,false);
m.expectCommand('referenciar RETO','Referencia MANUAL aceita.');
m.expectCommand('armar','ARMADO.');
m.expectCommand('20;20','fora do alcance');
m.expectCommand('1;2;3','ERRO');
m.expectCommand('nan;0','ERRO');
m.expectCommand('a'.repeat(90),'linha longa');
assert.deepEqual(m.counts,[0,0,0]);
console.log('PASS: sem referencia, intertrava aberta e entradas invalidas nao movem.');

for(const [n,expected] of [[3,[0,0,84]],[4,[42,127,190]],[6,[127,84,169]],[1,[0,0,0]],[5,[-42,-127,-190]]]) {
  const baseline=[...m.counts];
  m.order.length=0;
  m.expectCommand('caso '+n,'PREVIA');
  m.clear(); m.send('mover\n');
  m.until(()=>m.output.includes('TRAJETO DE PULSOS CONCLUIDO'),60); m.run(.04);
  assert.deepEqual(m.counts,expected,'destinos reais nos GPIO, caso '+n);
  assert(m.starts.every(x=>x===null),'pulso nao encerrado');
  assert.deepEqual(m.order,[0,1,2].filter(i=>expected[i]!==baseline[i]),'ordem deve ser M1, M2, M3');
  console.log('PASS: caso '+n+' -> GPIO '+m.counts.join(';')+'; ordem '+m.order.map(i=>'M'+(i+1)).join('->'));
  if(n===4) {
    const before=[...m.counts];
    m.expectCommand('caso 5','PREVIA');
    m.expectCommand('mover','etapa M1/M2/M3 excede');
    assert.deepEqual(m.counts,before);
    console.log('PASS: transicao 4->5 bloqueada antes dos pulsos por flexao intermediaria.');
  }
}
assert(m.minWidth>=40,'pulso ativo menor que 40 us');
assert(m.minPeriod>=16000,'frequencia acima do limite conservador');
console.log(`PASS: menor LOW=${m.minWidth.toFixed(2)} us; menor periodo=${m.minPeriod.toFixed(2)} us.`);

m=machine(unlockedFile);
m.expectCommand('referenciar RETO','Referencia MANUAL aceita.');
m.expectCommand('armar','ARMADO.');
m.expectCommand('caso 2','PREVIA'); m.send('mover\n');
m.until(()=>m.counts.some(x=>x!==0),3);
m.send('!'); m.until(()=>m.output.includes('Referencia INVALIDADA'),2); m.run(.05);
const stopped=[...m.counts]; m.run(.4); assert.deepEqual(m.counts,stopped);
assert(m.starts.every(x=>x===null));
m.expectCommand('mover','BLOQUEADO');
console.log('PASS: ! encerra pulso, para, desarma e exige nova referencia.');

m.expectCommand('referenciar RETO','Referencia MANUAL aceita.');
m.expectCommand('armar','ARMADO.');
m.expectCommand('caso 6','PREVIA'); m.send('mover\n');
const baseline=[...m.counts]; m.until(()=>m.counts.some((v,i)=>v!==baseline[i]),3);
m.b.setPin(0,true); m.clear();
m.until(()=>m.output.includes('intertrava aberta.'),2); m.run(.1);
const interlocked=[...m.counts]; m.run(.4); assert.deepEqual(m.counts,interlocked);
assert(m.starts.every(x=>x===null));
m.expectCommand('armar','BLOQUEADO');
console.log('PASS: abertura de D8 interrompe e impede rearmar.');
console.log('Emulacao do firmware aprovada. Nao valida driver, motores, cabos ou seguranca fisica.');
