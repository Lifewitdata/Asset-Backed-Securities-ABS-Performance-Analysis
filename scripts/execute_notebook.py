"""Execute all notebook cells; --in-process avoids kernel sockets in restricted hosts."""
import argparse
import os
from pathlib import Path
import nbformat


def execute_in_process(nb):
    import io
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display,Image
    shell=InteractiveShell.instance()
    def show(*args,**kwargs):
        for number in plt.get_fignums():
            buf=io.BytesIO()
            plt.figure(number).savefig(buf,format='png',bbox_inches='tight',dpi=110)
            display(Image(data=buf.getvalue()))
        plt.close('all')
    plt.show=show
    count=0
    for cell in nb.cells:
        if cell.cell_type!='code':continue
        count+=1
        with capture_output(stdout=True,stderr=True,display=True) as captured:
            result=shell.run_cell(cell.source,store_history=True)
        result.raise_error()
        cell.execution_count=count
        cell.outputs=[]
        if captured.stdout:cell.outputs.append(nbformat.v4.new_output('stream',name='stdout',text=captured.stdout))
        if captured.stderr:cell.outputs.append(nbformat.v4.new_output('stream',name='stderr',text=captured.stderr))
        for output in captured.outputs:
            cell.outputs.append(nbformat.v4.new_output('display_data',data=output.data,metadata=output.metadata))
    nb.metadata['execution_method']='IPython in-process; all code cells executed sequentially'


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--in-process',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    path=root/'notebooks/01_abs_quantitative_research.ipynb'
    nb=nbformat.read(path,as_version=4)
    if args.in_process:
        os.chdir(root)
        execute_in_process(nb)
    else:
        from nbclient import NotebookClient
        NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(root)}}).execute()
        nb.metadata['execution_method']='Jupyter kernel via nbclient'
    nbformat.validate(nb)
    nbformat.write(nb,path)
    print('Notebook executed successfully.')
