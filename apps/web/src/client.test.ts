import {expect,test} from 'vitest';
import {defaults,validDraft} from './client';
test('composer validation counts Unicode code points and preserves lyric byte bounds',()=>{
 const draft={...defaults,brief:'🎵'.repeat(500)};expect(validDraft(draft)).toBe(true);expect(validDraft({...draft,brief:draft.brief+'a'})).toBe(false);
 expect(validDraft({...draft,lyrics:{mode:'user',text:'  \n'}})).toBe(false);
 expect(validDraft({...draft,lyrics:{mode:'user',text:'தமிழ்\nहवा 🎵'}})).toBe(true);
 expect(validDraft({...draft,lyrics:{mode:'user',text:'a'.repeat(20001)}})).toBe(false);
 expect(validDraft({...draft,seed:1.2})).toBe(false);expect(validDraft({...draft,duration_seconds:31})).toBe(false);
});
