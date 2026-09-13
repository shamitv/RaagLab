import {useEffect, useRef, useState} from 'react';
import type {Version} from './client';
export function time(value:number) {return `${Math.floor(value/60)}:${String(Math.floor(value%60)).padStart(2,'0')}`;}
export function Player({version, collection, select, disabled}:{version:Version;collection:string[];select:(id:string)=>void;disabled:boolean}) {
  const audio=useRef<HTMLAudioElement>(null);
  const [elapsed,setElapsed]=useState(0), [duration,setDuration]=useState(0), [playing,setPlaying]=useState(false);
  const [volume,setVolume]=useState(.8), [repeat,setRepeat]=useState(0), [shuffle,setShuffle]=useState<string[] | null>(null), [error,setError]=useState('');
  useEffect(()=>{setElapsed(0);setDuration(0);setPlaying(false);setError('');},[version.id]);
  const order=shuffle && shuffle.length === collection.length && shuffle.every(id=>collection.includes(id)) ? shuffle : collection;
  const index=order.indexOf(version.id);
  function move(delta:number) {const next=index+delta; if(next>=0 && next<order.length) select(order[next]);else if(repeat===2) select(order[(next+order.length)%order.length]);}
  async function play() {try {await audio.current?.play();} catch {setError('Playback could not start. Try Play again.');}}
  return <section className="card player" aria-label="Music Preview"><h2>Music Preview</h2><h3>{version.label}</h3><p className="muted">{String(version.inputs.genre)} · {String(version.inputs.language)} · Original demo</p>
    <audio ref={audio} key={version.id} preload="metadata" src={version.audio.url} onLoadedMetadata={()=>{setDuration(audio.current!.duration);audio.current!.volume=volume;}} onTimeUpdate={()=>setElapsed(audio.current!.currentTime)} onPlay={()=>setPlaying(true)} onPause={()=>setPlaying(false)} onError={()=>setError('Audio is unavailable. Choose another version deliberately; your lyrics remain saved.')} onEnded={()=>{setPlaying(false);if(repeat===1){audio.current!.currentTime=0;void play();}else if(repeat===2) move(1);}}/>
    <label>Seek<input type="range" min="0" max={duration || 0} step="0.01" value={elapsed} disabled={!duration} aria-valuetext={`${time(elapsed)} of ${time(duration)}`} onChange={e=>{audio.current!.currentTime=Number(e.target.value);setElapsed(Number(e.target.value));}}/></label>
    <p className="time">{time(elapsed)} / {duration ? time(duration) : 'Loading audio…'}</p>
    <div className="actions playback"><button disabled={disabled || collection.length<2} title="Shuffle project versions" aria-pressed={!!shuffle} onClick={()=>setShuffle(shuffle ? null : collection.map(id=>({id,sort:Math.random()})).sort((a,b)=>a.sort-b.sort).map(x=>x.id))}>Shuffle</button><button disabled={disabled || collection.length<2 || (index===0 && repeat!==2)} onClick={()=>move(-1)}>Previous</button><button className="primary" disabled={!!error || !duration} onClick={()=>playing ? audio.current?.pause() : void play()}>{playing?'Pause':'Play'}</button><button disabled={disabled || collection.length<2 || (index===order.length-1 && repeat!==2)} onClick={()=>move(1)}>Next</button><button onClick={()=>setRepeat((repeat+1)%3)}>Repeat: {['off','one','collection'][repeat]}</button></div>
    {collection.length<2 && <small>Previous, next and shuffle need two completed versions.</small>}
    <label>Volume<input type="range" min="0" max="1" step=".01" value={volume} onChange={e=>{setVolume(Number(e.target.value));audio.current!.volume=Number(e.target.value);}}/></label>
    <a className="button-link" href={version.audio.url} download={`museforge-${version.id}.wav`}>Download WAV</a>{!version.audio_recomposed && <p>Audio unchanged — this version edits lyrics only.</p>}{error && <p role="alert">{error}</p>}
  </section>;
}
