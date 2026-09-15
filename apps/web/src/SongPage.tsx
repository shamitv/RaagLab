import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import QRCode from "qrcode";
import type { Version } from "./client";
import { api } from "./client";
import { Player } from "./Player";

export function SongPage() {
  const { id = "" } = useParams();
  const [song, setSong] = useState<Version | null>(null);
  const [base, setBase] = useState<string | null>(null);
  const [qr, setQr] = useState("");
  const [message, setMessage] = useState("");
  useEffect(() => {
    Promise.all([api<Version>(`/api/v1/versions/${id}`), api<{song_link_base_url: string | null}>("/api/v1/frontend-config")])
      .then(([version, config]) => { setSong(version); setBase(config.song_link_base_url); })
      .catch((error) => setMessage((error as Error).message));
  }, [id]);
  const url = base && song ? `${base}/songs/${song.id}` : "";
  useEffect(() => { if (url) void QRCode.toDataURL(url, { width: 280, margin: 2 }).then(setQr); }, [url]);
  if (!song) return <p role={message ? "alert" : "status"}>{message || "Loading song…"}</p>;
  async function favorite() {
    const next = await api<Version>(`/api/v1/versions/${song!.id}`, { method: "PATCH", body: JSON.stringify({favorite: !song!.favorite}), headers: {"If-Match": `"${song!.revision}"`} });
    setSong(next);
  }
  return <section className="song-page">
    <Player version={song} collection={[song.id]} select={async () => true} disabled={false} />
    <div className="card"><h2>Lyrics</h2><pre className="lyrics-readonly">{song.lyrics}</pre></div>
    <div className="card"><h2>Keep this song</h2>{url ? <><img className="song-qr" src={qr} alt="QR code for this song"/><p><a href={qr} download={`museforge-${song.id}.png`}>Download QR</a></p><button onClick={() => void navigator.clipboard.writeText(url).then(() => setMessage("Song link copied."))}>Copy link</button><p role="status">{message}</p></> : <p>Set SONG_LINK_BASE_URL to a reachable address to create a phone-friendly QR code.</p>}</div>
    <div className="actions"><button aria-pressed={song.favorite} onClick={() => void favorite()}>{song.favorite ? "Unfavorite" : "Favorite"}</button><Link className="button-link" to={`/projects/${song.project_id}?version=${song.id}`}>Create another version</Link><a className="button-link" href={song.audio.url} download>Download audio</a></div>
  </section>;
}
